import getopt
import os
import re
import sys
from jinja2 import Environment as JinjaEnvironment
from jinja2.loaders import FileSystemLoader

class LazyProperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value


class CaseModel(object):
    pattern = re.compile('\\((.*?)\)')

    def __init__(self, case, path, pattern, parameters):
        self.name = case
        self.path = path
        self.pattern = pattern
        self.parameters = parameters

    def __str__(self):
        return """
            name: {name},
            path: {path},
            pattern: {pattern},
            parameters: {parameters}
        """.format(name=self.name, pattern=self.pattern, path=self.path, parameters=self.parameters)

    @LazyProperty
    def has_parameters_in_path(self):
        return self.parameter_str_in_path is not None

    @LazyProperty
    def parameter_str_in_path(self):
        parameters_in_path = re.findall(CaseModel.pattern, self.path)
        if not self.parameters or not parameters_in_path:
            return None
        all_parameters_placeholder = ['_'] * len(self.parameters)
        for i in range(len(parameters_in_path)):
            all_parameters_placeholder[i] = parameters_in_path[i]

        parameters = ', '.join(all_parameters_placeholder)
        return parameters

    @LazyProperty
    def parameters_str(self):
        return ', '.join([x[0] for x in self.parameters])

    def _has_optional_parameter(self):
        for (_, value) in self.parameters:
            if value.endswith('?'):
                return True


class RouterEntity(object):
    """
        parse all case for one swift enum type
    """
    pattern = re.compile('@pattern(.*?)\s+case\s+(\w*)\(?(.*)\)?')

    def __init__(self, name, content):
        """
        :param name: the swift enum name
        :param content: the swift enum content case
        """
        self.name = name
        self._content = content
        self.case_models = list(self._parse_to_case())
        self.has_no_parameter_case = next((case for case in self.case_models if not case.parameters), None) is not None

    def _parse_to_case(self):
        cases = re.findall(RouterEntity.pattern, self._content)
        for case in cases:
            parameters = []
            url_pattern = case[0]
            if not url_pattern:
                url_pattern = "/" + camel_to_snake(case[1])
            if case[2]:
                parameters = self._parse_parameter(case[2])
            yield CaseModel(
                pattern=url_pattern.strip(),
                path=self._parse_path(url_pattern).strip(),
                case=case[1].strip(),
                parameters=parameters
            )

    def _parse_path(self, url_pattern):
        str = ''
        for item in url_pattern.split('/'):
            if not item.strip(): continue
            if item.startswith(':'):
                item = "\({p})".format(p=item[1:])
            str += '/' + item
        return str

    def _parse_parameter(self, str):
        str = str.strip()
        if not str:
            return None

        _tuples = []
        for s in str.split(', '):
            key, value = map(lambda x: x.strip(), s.split(": "))
            _tuples.append((camel_to_snake(key), value))
        return _tuples


def snake_to_camel(snake_format):
     camel_format = ''
     if isinstance(snake_format, str):
         for _s_ in snake_format.split('_'):
             camel_format += _s_.capitalize()
     return camel_format[:1].lower() + camel_format[1:]


def camel_to_snake(camel_format):
    snake_format=''
    if isinstance(camel_format, str):
        for _s_ in camel_format:
            snake_format += _s_ if _s_.islower() else '_'+_s_.lower()
    return snake_format


def parse_file(text):
    route_enum_pattern = re.compile('(?:@name\s+(.+?)\s+|enum\s+(\w+):?[^\n]*?\{)(.*?)\}', re.S)
    cases = re.findall(route_enum_pattern, text)
    for case in cases:
        content = case[2].strip()
        name = case[0]
        if not name:
            name = case[1]
        yield RouterEntity(name=name, content=content)


def parse_args():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hi:o:t:', ['input=', 'output=', 'tmpl='])
    except getopt.GetoptError:
        print('Error: -i <inputfile> -o [outputfile]')
        print('or: -input <inputfile> -output [outputfile]')
        exit()

    template = 'tmpl'
    output_file = ''

    for opt, arg in opts:
        if opt == "-h":
            print('-i <inputfile> -o [outputfile] -t [template]')
            print('or: -input <inputfile> --output [outputfile] --tmpl [template]')
            exit()
        elif opt in ('-i', '--input'):
            input_file = arg
        elif opt in ('-o', '--output'):
            output_file = arg
        elif opt in ('-t', '--template'):
            template = arg

    if input_file and not output_file:
        output_file = os.path.dirname(input_file) + '/Router.Generate.swift'

    if not input_file or not output_file:
        print('miss input file: -i <inputfile> or: -input <inputfile>')
        print('')

    return (input_file, output_file, template)

if __name__ == '__main__':
    input_file, output_file, template = parse_args()

    with open(input_file, 'r', encoding='utf-8') as f1, open(output_file, 'wt') as f2:
        text = f1.read()
        env = JinjaEnvironment(line_statement_prefix="#", loader=FileSystemLoader(searchpath=['./tmpl', 'Pods/RGenerator/tmpl']))
        tmpl = env.get_template(template)
        models = [(item.name, item.case_models, item.has_no_parameter_case) for item in parse_file(text)]
        text = tmpl.render(models=models, snake_to_camel=snake_to_camel)
        f2.write(text)
