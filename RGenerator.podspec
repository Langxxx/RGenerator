Pod::Spec.new do |s|
  s.name         = "RGenerator"
  s.version      = "0.1.0"
  s.summary      = "Got a convenient way to manage router in swift project"
  s.homepage     = "https://github.com/Langxxx/RGenerator"
  s.license      = "MIT"
  s.author       = { "Langxxx" => "wxl19950606@163.com" }
  s.source       = { :http => "https://github.com/Langxxx/RGenerator/releases/download/#{s.version}/RGenerator.zip" }
  s.preserve_paths = "generate", "tmpl/*"
end
