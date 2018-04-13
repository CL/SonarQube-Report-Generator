import urllib.request
import json


def main():
    config = get_config()
    template = get_template(config)
    measures = get_measures(config)
    generate_report(template, measures)


def get_config():
    with open('config.json', 'r', encoding="utf8") as configFile:
        config_string = configFile.read()
    return json.loads(config_string)


def generate_report(template, measures):
    for metric in measures['component']['measures']:
        template = template.replace('__'+metric['metric']+'__', metric['value'])
    report = open("report.md", "w+", encoding="utf8")
    report.writelines(template)
    report.close()


def get_measures(config):
    project_id = get_project_id(config)
    request = urllib.request.Request(config['url']+'/api/measures/component?componentId='+id+'&metricKeys=code_smells,bugs,vulnerabilities,coverage&additionalFields=metrics,periods')
    request.add_header('Authorization', 'Basic MThlZWM0MTVkNjFiZmNiZjg1YmMwY2Q3YzRiNmNlY2FhYjE1NjY5Mzo=')

    return json.loads(urllib.request.urlopen(req).read())


def get_project_id(config):
    request = urllib.request.Request(config['url'] + '/api/components/show?key=' + config['project_name'])
    request.add_header('Authorization', 'Basic MThlZWM0MTVkNjFiZmNiZjg1YmMwY2Q3YzRiNmNlY2FhYjE1NjY5Mzo=')
    return json.loads(urllib.request.urlopen(request).read())['component']['id']


def get_template(config):
    with open(config['template'], 'r', encoding="utf8") as templateFile:
        template = templateFile.read()
    return template


if __name__ == "__main__":
    main()



