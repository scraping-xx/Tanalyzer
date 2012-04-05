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
</div>
{% endblock %}

{% block content %}
<div id="content" class="colMS">
    <form method='POST'>
    {% csrf_token %}
    <h1>Clasificación Manual</h1>
        <div id='document'>
            
           <select name='ldamodel'>
           {% for ldamodel in ldamodels %}
                <option value='{{ldamodel.id}}'>{{ldamodel.name}}</option>
           {% endfor %}
           </select>

        </div>
        <br/>
        <input type='submit' class='button' name='send' value='Go' />
    </form>

</div>
{% endblock %}








