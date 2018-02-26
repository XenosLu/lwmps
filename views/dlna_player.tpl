{% extends base.tpl %}
{% block title %}DMC - Light Media Player{% end %}

    {% block main %}
      {% include common.tpl %}
      {% include dlna.tpl %}
    {% end %}

{% block script %}
<script src="{{ static_url('js/dlna.js') }}"></script>
{% end %}
