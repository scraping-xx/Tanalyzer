{% extends "admin/base_site.html" %}
{% load i18n %}

{% block coltype %}colMS{% endblock %}
{% block adm_on %}{%endblock%}
{% block csf_on %}current{%endblock%}
{% block bodyclass %}dashboard{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs">
    <a href="/application/">Home</a>
    &rsaquo; Classifier
</div>
{% endblock %}

{% block content %}
<script type='text/javascript'>
$(document).ready(function(){});
</script>



<div id="content" class="colMS">
<br/>

{% if classifiers %}
    <h1>Selecciona un clasificador e ingresa un texto</h1>
    <br/>
    <table>
        <tr>
            <td>
                <form method = "post" action="">
                	{% csrf_token %}
                	<fieldset>
                    <input type='hidden' name='process' value='one_text' />
                    <label for='classifier'>Classificador</label>
                    <select name='classifier'>
                    {% for classifier in classifiers %}
                        <option value='{{classifier.id}}'>{{classifier.name}}</option>
                    {% endfor %}
                    </select>
                    <br/>
                    <br/>
                    <label for='text'>Texto</label><br/>
                    <textarea name='text'>{%if text%}{{text}}{%endif%}</textarea>

                    <br/>
                    <input type="submit" name="send" value="Start!">
                    </fieldset>
                </form>
            </td>
            {% if json %}
            <td>
                    <div class="response">
                        Json Output:<br/>
                        <pre>{{json}}</pre>
                    </div>
                    <ul>
                    {% for element in jsoneval.cat %}
                        <li>
                            {{element.topic_label}} &rarr; 
                            {% if element.value > 10 %}<strong>{{element.value}}%</strong>
                            {% else %} {{element.value}}% 
                            {% endif %} 
                            {% if element.value > 10 and element.subtopics %} 
                                <ul> 
                                {% for subelement in element.subtopics %} 
                                    <li>
                                    {{subelement.topic_label}} &rarr;
                                    {% if subelement.value > 10 %}<strong>{{subelement.value}}%</strong>
                                    {% else %} {{subelement.value}}% 
                                    {% endif %}  
                                    </li>
                                {% endfor %}
                                </ul> 
                            {% endif %}
                        </li>
                        
                    {% endfor %}
                    </ul>
            </td>
            {% endif %}
        </tr>
    </table>
    <h1>Selecciona un dataset para predecir</h1>
    <br/>
    <form method = "post" action="">
        {% csrf_token %}
        <fieldset>
        <input type='hidden' name='process' value='one_dataset' />
        <label for='classifier'>Classificador</label>
        <select name='classifier'>
        {% for classifier in classifiers %}
            <option value='{{classifier.id}}'>{{classifier.name}}</option>
        {% endfor %}
        </select>
        <label for='dataset'>Dataset</label>
        <select name='dataset'>
        {% for dataset in datasets %}
            <option value='{{dataset.id}}'>{{dataset.name}}</option>
        {% endfor %}
        </select>
        <input type='checkbox' name='only_test_data' checked='checked'> Only classify test data. 
        <br/>
        <br/>
        <input type="submit" name="send" value="Classify!">
        </fieldset>
    </form>
    <h1>Selecciona un ldamodel para predecir</h1>
    <br/>
    <form method = "post" action="">
        {% csrf_token %}
        <fieldset>
        <input type='hidden' name='process' value='one_ldamodel' />
        <label for='classifier'>Classificador</label>
        <select name='classifier'>
        {% for classifier in classifiers %}
            <option value='{{classifier.id}}'>{{classifier.name}}</option>
        {% endfor %}
        </select>
        <label for='ldamodel'>Ldamodel</label>
        <select name='ldamodel'>
        {% for ldamodel in ldamodels %}
            <option value='{{ldamodel.id}}'>{{ldamodel.name}}</option>
        {% endfor %}
        </select>
        <input type='checkbox' name='only_test_data' checked='checked'> Only classify test data. 
        <br/>
        <br/>
        <input type="submit" name="send" value="Classify!">
        </fieldset>
    </form>
{% else %}
    <p>No hay Clasificadores!.</p>
{% endif %}
</div>

{% endblock %}







