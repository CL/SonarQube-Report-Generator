import urllib.request
import json
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import jinja2
import markdown
from email.mime.base import MIMEBase
from email import encoders


TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
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


def main():
    config = get_config()
    template = get_template(config)
    header_template = get_header_template(config)
    measures = get_measures(config)
    issues = get_issues(config)
    html = generate_report(header_template, template, measures, issues, config)
    message = make_email_message(config, html)
    send_email(config, message)


def markdown_2_html(report):
    extensions = ['extra', 'smarty']
    html = markdown.markdown(report, extensions=extensions, output_format='html5')
    doc = jinja2.Template(TEMPLATE).render(content=html)
    return doc


def make_email_message(config, html):
    subject = 'SonarReport - ' + datetime.datetime.now().strftime('%d/%m/%Y') + ' - ' + config['project_name']

    message = MIMEMultipart('alternative')
    message['From'] = config['email_from']
    message['To'] = ", ".join(config['email_to'])
    message['Subject'] = subject
    message.attach(MIMEText(html, 'html'))

    csv_part = MIMEBase('application', "octet-stream")
    csv_part.set_payload(open(config['output_csv'], "rb").read())
    encoders.encode_base64(csv_part)
    csv_part.add_header('Content-Disposition', 'attachment; filename="' + config['output_csv'] + '"')
    message.attach(csv_part)

    md_part = MIMEBase('application', "octet-stream")
    md_part.set_payload(open(config['output'], "rb").read())
    encoders.encode_base64(md_part)
    md_part.add_header('Content-Disposition', 'attachment; filename="' + config['output'] + '"')
    message.attach(md_part)

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


def generate_report(header_template, template, measures, issues, config):
    for metric in measures['component']['measures']:
        template = template.replace('__'+metric['metric']+'__', metric['value'])
        header_template = header_template.replace('__' + metric['metric'] + '__', metric['value'])

    header_template = header_template.replace('__date__', datetime.datetime.now().strftime('%d/%m/%Y'))
    header_template = header_template.replace('__project_name__', measures['component']['name'])
    template = template.replace('__date__', datetime.datetime.now().strftime('%d/%m/%Y'))
    template = template.replace('__project_name__', measures['component']['name'])

    vulnerabilities_critical = generate_issues_report(config, issues, 'CRITICAL', 'VULNERABILITY')
    vulnerabilities_major = generate_issues_report(config, issues, 'MAJOR', 'VULNERABILITY')
    vulnerabilities_minor = generate_issues_report(config, issues, 'MINOR', 'VULNERABILITY')
    vulnerabilities_blocker = generate_issues_report(config, issues, 'BLOCKER', 'VULNERABILITY')
    vulnerabilities_info = generate_issues_report(config, issues, 'INFO', 'VULNERABILITY')

    bugs_critical = generate_issues_report(config, issues, 'CRITICAL', 'BUG')
    bugs_major = generate_issues_report(config, issues, 'MAJOR', 'BUG')
    bugs_minor = generate_issues_report(config, issues, 'MINOR', 'BUG')
    bugs_blocker = generate_issues_report(config, issues, 'BLOCKER', 'BUG')
    bugs_info = generate_issues_report(config, issues, 'INFO', 'BUG')

    smells_critical = generate_issues_report(config, issues, 'CRITICAL', 'CODE_SMELL')
    smells_major = generate_issues_report(config, issues, 'MAJOR', 'CODE_SMELL')
    smells_minor = generate_issues_report(config, issues, 'MINOR', 'CODE_SMELL')
    smells_blocker = generate_issues_report(config, issues, 'BLOCKER', 'CODE_SMELL')
    smells_info = generate_issues_report(config, issues, 'INFO', 'CODE_SMELL')

    template = template.replace('__vulnerabilities_critical_issues__', vulnerabilities_critical[0])
    template = template.replace('__vulnerabilities_major_issues__', vulnerabilities_major[0])
    template = template.replace('__vulnerabilities_minor_issues__', vulnerabilities_minor[0])
    template = template.replace('__vulnerabilities_blocker_issues__', vulnerabilities_blocker[0])
    template = template.replace('__vulnerabilities_info_issues__', vulnerabilities_info[0])

    template = template.replace('__bugs_critical_issues__', bugs_critical[0])
    template = template.replace('__bugs_major_issues__', bugs_major[0])
    template = template.replace('__bugs_minor_issues__', bugs_minor[0])
    template = template.replace('__bugs_blocker_issues__', bugs_blocker[0])
    template = template.replace('__bugs_info_issues__', bugs_info[0])

    template = template.replace('__smells_critical_issues__', smells_critical[0])
    template = template.replace('__smells_major_issues__', smells_major[0])
    template = template.replace('__smells_minor_issues__', smells_minor[0])
    template = template.replace('__smells_blocker_issues__', smells_blocker[0])
    template = template.replace('__smells_info_issues__', smells_info[0])

    report = open(config['output'], "w+", encoding="utf8")
    report.writelines(template)
    report.close()

    csv = 'TIPO,SEVERIDADE,DESCRICAO,ARQUIVO,LINHA(S)\n'
    csv = csv + vulnerabilities_blocker[1]
    csv = csv + vulnerabilities_critical[1]
    csv = csv + vulnerabilities_major[1]
    csv = csv + vulnerabilities_minor[1]
    csv = csv + vulnerabilities_info[1]
    csv = csv + bugs_blocker[1]
    csv = csv + bugs_critical[1]
    csv = csv + bugs_major[1]
    csv = csv + bugs_minor[1]
    csv = csv + bugs_info[1]
    csv = csv + smells_blocker[1]
    csv = csv + smells_critical[1]
    csv = csv + smells_major[1]
    csv = csv + smells_minor[1]
    csv = csv + smells_info[1]

    report = open(config['output_csv'], "w+", encoding="utf8")
    report.writelines(csv)
    report.close()

    html = markdown_2_html(header_template)

    return html


def generate_issues_report(config, issues, severity, issue_type):
    report = ''
    csv = ''
    for issue in issues:
        report = report + generate_issue_string(config, issue, severity, issue_type)[0]
        csv = csv + generate_issue_string(config, issue, severity, issue_type)[1]
    return [report, csv]



def generate_issue_string(config, issue, severity, issue_type):
    report = ''
    csv = ''
    if issue['type'] == issue_type and issue['severity'] == severity:
        file_name = issue['component'].replace(config['project_name'] + ':', '').split(":", 1)[1]
        csv = issue_type + ',' + severity + ',"' + issue['message'] + '",' + file_name + ','
        report = report + '\n\n >##### Descricao: \n>' + issue['message'] + '\n>###### Arquivo: ' + file_name

        try:
            if issue['textRange']['startLine'] == issue['textRange']['endLine']:
                csv = csv + str(issue['textRange']['startLine'])
                report = report + '\n>###### Linha: ' + str(issue['textRange']['startLine'])
            else:
                csv = csv + str(issue['textRange']['startLine']) + ' - ' + str(issue['textRange']['endLine'])
                report = report + '\n>###### Linhas: ' + str(issue['textRange']['startLine']) + ' - ' + str(issue['textRange']['endLine'])
        except:
            csv = csv + 'Linha desconhecida'
            report = report + '\n>###### Linha desconhecida'
        csv = csv + '\n'
    return [report, csv]


def get_measures(config):
    project_id = get_project_id(config)
    request = urllib.request.Request(config['url']+'/api/measures/component?componentId='+project_id+'&metricKeys='+config['metrics']+'&additionalFields=metrics,periods')
    request.add_header('Authorization', 'Basic ' + config['token'])
    return json.loads(urllib.request.urlopen(request).read())


def get_issues(config):
    response = get_issues_page(config, 1)
    issues = response['issues']
    if response['total'] > 100:
        total = response['total']
        current_total = len(issues)
        page_counter = 1
        while total > current_total and page_counter < 100:
            page_counter += 1
            response = get_issues_page(config, page_counter)
            current_total += len(response['issues'])
            issues.extend(response['issues'])
    return issues


def get_issues_page(config, page):
    request = urllib.request.Request(
        config['url'] + '/api/issues/search?statuses=OPEN,REOPENED&componentKeys=' + config['project_name'] + '&p=' + str(page))
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


def get_header_template(config):
    with open(config['header_template'], 'r', encoding="utf8") as templateFile:
        header_template = templateFile.read()
    return header_template


if __name__ == "__main__":
    main()
