{% if score >= 9.0 %}■■■■■{% elif score >=8.0 %}■■■□□{% elif score >= 7.0 %}■■□□□{% elif score <= 6.9 %}■□□□□{% else %}□□□□□{% endif %} {{type}} - {{name}} - ({% if source %} {{source}} {% else %} None {% endif %})

{{description}}

Severity: {{baseSeverity}}
Score: {{score}}
Vendor: {{vendor}}
Published Date: {{publishedDate}}
Last Modified Date: {{lastModifiedDate}}
Scope: {{scope}}
User Interaction: {{userInteraction}}
References: {{references}}
URL: https://nvd.nist.gov/vuln/detail/{{name}}
