import commonmark


def md2html(md_text):
    html_text = commonmark.commonmark(md_text)
    return html_text


def url(name, url):
    if url:
        return f'<a href="{url}">{name}</a>'
    return name


def colorize(text, color=None):
    css_color = '#ffffff'
    if color:
        css_color = f'#{hex(int(color))[2:]}'

    return f'<font color="{css_color}">{text}</font>'


def strong(text):
    return f'<strong>{text}</strong>'
