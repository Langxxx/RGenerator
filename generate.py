import getopt
import re

import sys


class LazyProperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(owner, self.func.__name__, value)
            return value


class CaseModel(object):
    pattern = re.compile('\\((.*?)\)')

    def __init__(self, case, path, pattern, parameters):
        self.case = case
        self.path = path
        self.pattern = pattern
        self.parameters = parameters

    def __str__(self):
        return """
            name: {name},
            path: {path},
            pattern: {pattern},
            parameters: {parameters}
        """.format(name=self.case, pattern=self.pattern, path=self.path, parameters=self.parameters)

    def case_description(self):
        return 'case .' + self.case

    def pattern_description(self):
        return '''
    public static var {case}Pattern: String {{
        return "{pattern}"
    }}
        '''.format(case=self.case, pattern=self.pattern)

    def path_description(self):
        parameters_in_path = re.findall(CaseModel.pattern, self.path)
        if not self.parameters or not parameters_in_path:
            return 'case .{case}: return "{path}"'.format(case=self.case, path=self.path)

        all_parameters_placeholder = ['_'] * len(self.parameters)
        for i in range(len(parameters_in_path)):
            all_parameters_placeholder[i] = parameters_in_path[i]

        parameters = ', '.join(all_parameters_placeholder)
        return 'case let .{case}({parameters}): return "{path}"'\
            .format(case=self.case, parameters=parameters, path=self.path)

    def _has_optional_parameter(self):
        for (_, value) in self.parameters:
            if value.endswith('?'):
                return True

    def parameter_description(self):
        if not self.parameters:
            return None
        p = [x[0] for x in self.parameters]
        str = 'case let case .{case}({parameters}):'.format(case=self.case, parameters=', '.join(p))
        if self._has_optional_parameter():
            str += '\n\t\t\tvar p: [String: Any] = [:]'
            for (k, v) in self.parameters:
                if v.endswith('?'):
                    str += '\n\t\t\tif let value = {attr} {{ p["{attr}"] = value }}'.format(attr=k)
                else:
                    str += '\n\t\t\tp["{k}"] = {k}'.format(k=k, v=v)
            str += '\n\t\t\treturn p'
            return str
        else:
            str += '\n\t\t\treturn ['
            for (k, v) in self.parameters:
                str += '\n\t\t\t\t"{key}": {key},'.format(key=k)
            return str + '\n\t\t\t]'

class RouterEntity(object):
    """
        parse all case for one swift enum type
    """
    pattern = re.compile('@pattern(.*?)\s+case\s+(.*?)\((.*?)\)')

    def __init__(self, name, content):
        """
        :param name: the swift enum name
        :param content: the swift enum content case
        """
        self.name = name
        self._content = content

    def router_description(self):
        cases = self._parse_to_case()
        path = '\tpublic var path: String {'
        path += '\n\t\tswitch self {'
        parameters = '\tpublic var parameter: String {'
        parameters += '\n\t\tswitch self {'
        pattern = ''
        for case in cases:
            path += '\n\t\t' + case.path_description()
            parameters += '\n\t\t' + case.parameter_description()
            pattern += case.pattern_description()
        path += '\n\t}'
        parameters += '\n\t}'

        result = 'extension {entity} {{\n'.format(entity=self.name)
        result += '\n'.join([path, parameters, pattern])
        result += '\n}\n'
        return result

    def _parse_to_case(self):
        cases = re.findall(RouterEntity.pattern, self._content)
        for case in cases:
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


def camel_to_snake(camel_format):
    snake_format=''
    if isinstance(camel_format, str):
        for _s_ in camel_format:
            snake_format += _s_ if _s_.islower() else '_'+_s_.lower()
    return snake_format


def parse_file(text):
    route_enum_pattern = re.compile('(?:@name\s+(.+?)\s+|enum\s+(\w+?)\s*:).*?\{(.*?)\}', re.S)
    cases = re.findall(route_enum_pattern, text)
    for case in cases:
        content = case[2].strip()
        name = case[0]
        if not name:
            name = case[1]
        yield RouterEntity(name=name, content=content)


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hi:o:', ['input=', 'output='])
    except getopt.GetoptError:
        print('Error: -i <inputfile> -o <outputfile>')
        print('or: -input <inputfile> -output <outputfile>')
        exit()

    for opt, arg in opts:
        if opt == "-h":
            print('-i <inputfile> -o <outputfile>')
            print('or: -input <inputfile> -output <outputfile>')
            exit()
        elif opt in ('-i', '--input'):
            input_file = arg
        elif opt in ('-o', '--output'):
            output_file = arg

    if not input_file or not output_file:
        print('Error: -i <inputfile> -o <outputfile>')
        print('or: -input <inputfile> -output <outputfile>')
        exit()

    with open(input_file, 'r') as f1, open(output_file, 'wt') as f2:
        text = f1.read()
        parse = '\n\n'.join([item.router_description() for item in parse_file(text)])
        f2.write(parse)
        