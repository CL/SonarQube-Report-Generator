# SonarQube Report Generator

Objetivo do programa é gerar relatórios customizáveis a partir dos indicadores do *SonarQube*

Ideal para e-mails de acompanhamento diário.

Como ele funciona: 

1) O script lê um arquivo de configuração para saber qual projeto ele vai gerar o relatório;
2) Depois ele usa a API do SonarQube para extrair os indicadores;
3) A partir de um template pré definido, ele insere os indicadores no local desejado e gera o output.

O template pode ser qualquer arquivo de texto. No meu caso um uso um arquivo markdown e depois gero um e-mail bonito e formatado usando o plugin [Markdown Here](https://markdown-here.com/).

Mas ele pode ser um arquivo .txt, pode ser um HTML, pode ser um script, o que for desejado...

Os indicadores podem ser qualquer um disponível no Sonar.

## Configuração

As configurações são feitas no arquivo config.json. Basicamente é necessário definir:

* URL do Sonar;
* [Token da API](https://docs.sonarqube.org/display/SONAR/User+Token) do Sonar;
* Nome do projeto no Sonar (aquele que vem depois do /k: na hora de criação);
* Nome do template;
* Metricas desejadas, separadas por vírgula;
* Nome do arquivo de saída.

Exemplo:
```json
{
  "url": "http://localhost:9000",
  "token": "MThlZWM0MTVkNjFiZmNiZjg1YmMwY2Q3YzRiNmNlY2FhYjE1NjY5Mzo=",
  "project_name": "Proj.test",
  "template": "template.md",
  "metrics": "code_smells,bugs,vulnerabilities,coverage",
  "output": "report.md"
}
```

## Template

O template pode ser qualquer arquivo de texto, os indicadores do Sonar devem estar escritos da seguinte forma `__nomeIndicador__` .
Além dos indicadores é possível usar a tag para substituir o nome do projeto: `__project_name__`

## Automatização

A automatização pode ser melhorada com um arquivo `.bat` para rodar a análise do sonar e logo em seguida o código python para geração e envio do relatório por email.

Exemplo:
```
@echo off
set REPOS_PATH=E:\sonarqube\sonarqube-7.0\msbuild
set SONNAR_SCANNER="%REPOS_PATH%\SonarQube.Scanner.MSBuild.exe"
set MS_BUILD="C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe"

cd "E:\local do projeto"
%SONNAR_SCANNER% begin /k:"ChaveProjeto" /n:"Nome projeto" /v:"1.0" /d:sonar.cs.opencover.reportsPaths="%CD%\opencover.xml"
%MS_BUILD% "Solution.sln" /t:Rebuild
"%LOCALAPPDATA%\Apps\OpenCover\OpenCover.Console.exe" -output:"%CD%\opencover.xml" -register:user -target:"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\Common7\IDE\CommonExtensions\Microsoft\TestWindow\vstest.console.exe" -targetargs:"Tests\MRV.Obras.Mobile.Domain.Tests\bin\Debug\MRV.Obras.Mobile.Domain.Tests.dll"
%SONNAR_SCANNER% end

C:
cd C:\Users\lucas\Desktop\sonar\SonarQube-Report-Generator\src
python generateReport.py
```
