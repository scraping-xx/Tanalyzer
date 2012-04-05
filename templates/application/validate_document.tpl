{% extends "admin/base_site.html" %}
{% load i18n %}

{% block coltype %}colMS{% endblock %}
{% block adm_on %}{%endblock%}
{% block val_on %}current{%endblock%}
{% block bodyclass %}dashboard{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs">
    <a href="/application/">Home</a> 
    &rsaquo; <a href="/application/validate/">Validate Data</a>
    &rsaquo; {{model.name}}
    &rsaquo; {{document.title}}
</div>
{% endblock %}

{% block content %}
<div id="content" class="colMS">
    <form method='POST'>
    {% csrf_token %}
        <h1>{{model.name}} ({{evaluated}}/{{total}})</h1>
        {% if document %}
        <h2>{{document.title}}</h2>
        <p>
            {% for p in prediction %}
                {% if p.value > 10 %} 
                    {{p.topic_label}} -> <b>{{p.value}}</b> -> {{p.quality}} <br/>
                {% endif %}
            {% endfor %}
        </p>

        <div id='document'>
            <p>{{document.original_content}}</p>
            <input type='hidden' name='document' value='{{document.id}}'> 
            {% for topic in topics %}
                <div class='word'><input type ='checkbox' name='topic' value='{{topic.id}}'> <label for='topic'>{{topic.label}}</label> </div>
            {% endfor %}
        </div>
        <br/>
        <input type='submit' class='button' name='send' value='Classify' />
        {% else %}
            <p>No quedan documentos por evaluar.</p>
        {% endif %}
    </form>
</div>
{% endblock %}








