import urllib.request
import json
import datetime
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from os.path import basename
from email.mime.text import MIMEText
import argparse
import sys
import jinja2
import markdown

def main():
    config = get_config()
    template = get_template(config)
    measures = get_measures(config)
    issues = get_issues(config)
    report = generate_report(template, measures, issues, config)
    message = make_email_message(config, 'SonarReport - '
                                 + datetime.datetime.now().strftime('%d/%m/%Y') + ' - ' + config['project_name'],
                                 report)
    send_email(config, message)


TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <link href="http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.0/css/bootstrap-combined.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
        }
        code, pre {
            font-family: monospace;
        }
        h1 code,
        h2 code,
        h3 code,
        h4 code,
        h5 code,
        h6 code {
            font-size: inherit;
        }
    </style>
</head>
<body>
<div class="container">
{{content}}
</div>
</body>
</html>
"""


def parse_args(args=None):
    d = 'Make a complete, styled HTML document from a Markdown file.'
    parser = argparse.ArgumentParser(description=d)
    parser.add_argument('mdfile', type=argparse.FileType('r'), nargs='?',
                        default=sys.stdin,
                        help='File to convert. Defaults to stdin.')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Output file name. Defaults to stdout.')
    return parser.parse_args(args)


def markdown_2_html(report):
    extensions = ['extra', 'smarty']
    html = markdown.markdown(report, extensions=extensions, output_format='html5')
    doc = jinja2.Template(TEMPLATE).render(content=html)
    return doc


def make_email_message(config, subject, report):
    message = MIMEMultipart('alternative')
    message['From'] = config['email_from']
    message['To'] = config['email_to']
    message['Subject'] = subject
    message.attach(MIMEText(markdown_2_html(report), 'html'))
    return message


def send_email(config, message):
    server = smtplib.SMTP(config['smtp_server'])
    server.ehlo()
    server.starttls()
    server.login(config['email_from'], config['email_from_password'])
    server.sendmail(config['email_from'], config['email_to'], message.as_string())
    server.close()


def get_config():
    with open('config.json', 'r', encoding="utf8") as configFile:
        config_string = configFile.read()
    return json.loads(config_string)


def generate_report(template, measures, issues, config):
    for metric in measures['component']['measures']:
        template = template.replace('__'+metric['metric']+'__', metric['value'])

    template = template.replace('__date__', datetime.datetime.now().strftime('%d/%m/%Y'))
    template = template.replace('__project_name__', measures['component']['name'])

    template = template.replace('__critical_issues__', generate_critical_issues_report(config, issues))
    template = template.replace('__major_issues__', generate_major_issues_report(config, issues))
    template = template.replace('__minor_issues__', generate_minor_issues_report(config, issues))
    template = template.replace('__blocker_issues__', generate_blocker_issues_report(config, issues))
    template = template.replace('__info_issues__', generate_info_issues_report(config, issues))

    report = open(config['output'], "w+", encoding="utf8")
    report.writelines(template)
    report.close()
    return template


def generate_major_issues_report(config, issues):
    report = ''
    for issue in issues['issues']:
        report = report + generate_issue_string(config, issue, 'MAJOR')
    return report


def generate_critical_issues_report(config, issues):
    report = ''
    for issue in issues['issues']:
        report = report + generate_issue_string(config, issue, 'CRITICAL')
    return report


def generate_minor_issues_report(config, issues):
    report = ''
    for issue in issues['issues']:
        report = report + generate_issue_string(config, issue, 'MINOR')
    return report


def generate_blocker_issues_report(config, issues):
    report = ''
    for issue in issues['issues']:
        report = report + generate_issue_string(config, issue, 'BLOCKER')
    return report


def generate_info_issues_report(config, issues):
    report = ''
    for issue in issues['issues']:
        report = report + generate_issue_string(config, issue, 'INFO')
    return report


def generate_issue_string(config, issue, severity):
    report = ''
    if issue['severity'] == severity and issue['project'] == config['project_name']:
        nome_arquivo = issue['component'].replace(config['project_name'] + ':', '').split(":", 1)[1]
        report = report + '\n\n >#### Descricao: \n>' + issue['message'] + '\n>##### Arquivo: ' + nome_arquivo
        try:
            if issue['textRange']['startLine'] == issue['textRange']['endLine']:
                report = report + '\n>##### Linha: ' + str(issue['textRange']['startLine'])
            else:
                report = report + '\n>##### Linhas: ' + str(issue['textRange']['startLine']) \
                         + ' - ' + str(issue['textRange']['endLine'])
        except:
            report = report + '\n>##### Linha desconhecida'
    return report


def get_measures(config):
    project_id = get_project_id(config)
    request = urllib.request.Request(config['url']+'/api/measures/component?componentId='+project_id+'&metricKeys='+config['metrics']+'&additionalFields=metrics,periods')
    request.add_header('Authorization', 'Basic ' + config['token'])
    return json.loads(urllib.request.urlopen(request).read())

def get_issues(config):
    request = urllib.request.Request(config['url']+'/api/issues/search')
    request.add_header('Authorization', 'Basic ' + config['token'])
    return json.loads(urllib.request.urlopen(request).read())


def get_project_id(config):
    request = urllib.request.Request(config['url'] + '/api/components/show?key=' + config['project_name'])
    request.add_header('Authorization', 'Basic ' + config['token'])
    return json.loads(urllib.request.urlopen(request).read())['component']['id']


def get_template(config):
    with open(config['template'], 'r', encoding="utf8") as templateFile:
        template = templateFile.read()
    return template


if __name__ == "__main__":
    main()




