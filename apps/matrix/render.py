from jinja2.sandbox import SandboxedEnvironment
from apps.matrix import filters

TEMPLATE = """
    {% if context.content %}
    {{ context.content|md2html|colorize }}
    {% endif %}
    {% if context.embeds %}
    {% for e in context.embeds %}
        <blockquote>
        <br/>
        <!-- author -->
        {% if e.author %}
            {{ e.author.name|url(e.author.url) }}
            <br/>
        {% endif %}
        {% if e.title %}
            {{ e.title|md2html|url(e.url)|colorize }}
        {% endif %}
        {% if e.description %}
            {{ e.description|md2html|colorize }}
        {% endif %}
        {% if e.fields %}
            {% for field in e.fields %}
                {{ field.name|strong|colorize }}
                <br/>
                {{ field.value|colorize }}
                <br/><br/>
            {% endfor %}
        {% endif %}
        {% if e.timestamp %}
            {{ e.timestamp|strong }}
        {% endif %}
        </blockquote>
        {{ "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"|colorize(e.color) }}
    {% endfor %}
    {% endif %}
"""


jinja_env = SandboxedEnvironment()
jinja_env.filters['md2html'] = filters.md2html
jinja_env.filters['url'] = filters.url
jinja_env.filters['colorize'] = filters.colorize
jinja_env.filters['strong'] = filters.strong
