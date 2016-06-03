from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import get_template
from ielex.extensional_semantics.forms import *
from ielex.extensional_semantics.models import *
from ielex.lexicon.models import Lexeme, Language
from ielex.forms import ChooseLanguageForm
from ielex.shortcuts import render_template
from ielex.utilities import confirm_required


# -- /relation(s)/ --------------------------------------------------------

def view_relation(request, relation):
    relation = SemanticRelation.objects.get(relation_code=relation)
    return render_template(request, "relation_view.html",
                           {"relation": relation})


@login_required
def edit_relation(request, relation):
    relation = SemanticRelation.objects.get(relation_code=relation)
    if request.method == 'POST':
        form = EditRelationForm(request.POST, instance=relation)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(relation.get_absolute_url())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(relation.get_absolute_url())
    else:
        form = EditRelationForm(instance=relation)
    return render_template(request, "relation_edit.html",
                           {"relation": relation,
                            "form": form})


@login_required
def add_relation(request):
    if request.method == 'POST':
        form = EditRelationForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(relation.get_absolute_url())
        if form.is_valid():
            form.save()
            relation = SemanticRelation.objects.get(
                    relation_code=form.cleaned_data["relation_code"])
            return HttpResponseRedirect(relation.get_absolute_url())
    else:
        form = EditRelationForm()
    return render_template(request, "relation_edit.html",
                           {"form": form,
                            "relation": "Add semantic relation"})

# -- semantic extensions --------------------------------------------------


def domains_list(request):
    domains = SemanticDomain.objects.all()
    return render_template(request, "domains_list.html", {"domains": domains})


def lexeme_domains_list(request, lexeme_id):
    lexeme = Lexeme.objects.get(id=int(lexeme_id))
    domain_ids = set(
        lexeme.semanticextension_set.values_list("relation", flat=True))
    domains = []
    for domain in SemanticDomain.objects.all():
        if set(domain.relation_id_list) & domain_ids:
            domains.append(domain)
    return render_template(request, 'lexeme_domains_list.html', {
            "lexeme": lexeme,
            "domains": domains})


def lexeme_extensions_view(request, lexeme_id):
    return render_template(request, 'lexeme_extensions_view.html', {
            "lexeme": Lexeme.objects.get(id=int(lexeme_id))})


def lexeme_domain_view(request, lexeme_id, domain, action="view"):
    """View and edit a lexeme's semantic extensions in a particular domain"""
    lexeme = Lexeme.objects.get(id=int(lexeme_id))
    try:
        sd = SemanticDomain.objects.get(name=domain)
    except SemanticDomain.DoesNotExist:
        raise Http404("SemanticDomain '%s' does not exist" % domain)
    tagged_relations = lexeme.semanticextension_set.filter(
        relation__id__in=sd.relation_id_list).values_list(
            "relation__id", flat=True)
    relations = SemanticRelation.objects.filter(
        id__in=SemanticDomain.objects.get(name=domain).relation_id_list
        ).values_list("id", "relation_code")
    if action == "edit":
        # TODO currently doesn't work....
        if request.method == "POST":
            form = AddSemanticExtensionForm(request.POST)
            citation_form = MultipleSemanticExtensionCitationForm(request.POST)
            if "cancel" in form.data:
                return HttpResponseRedirect(reverse("lexeme-domain-view",
                                                    args=[lexeme_id, domain]))
            if form.is_valid() and citation_form.is_valid():
                return_to = reverse("lexeme-domain-view",
                                    args=[lexeme_id, domain])
                original_relations = set(tagged_relations)
                new_relations = set(
                    int(e) for e in form.cleaned_data["relations"])
                removed_relations = original_relations.difference(
                    new_relations)
                added_relations = new_relations.difference(original_relations)
                if removed_relations:
                    SemanticExtension.objects.filter(
                        lexeme=lexeme,
                        relation__id__in=removed_relations).delete()
                if added_relations:
                    relations = SemanticRelation.objects.filter(
                        id__in=added_relations)
                    for relation in relations:
                        extension = SemanticExtension.objects.create(
                            lexeme=lexeme, relation=relation)
                        citation_form.extension = extension
                        citation_form.save()
                return HttpResponseRedirect(return_to)
        else:
            form = AddSemanticExtensionForm()
            form.fields["relations"].choices = relations
            form.fields["relations"].initial = tagged_relations
            citation_form = MultipleSemanticExtensionCitationForm()
    else:
        assert action == "view"
        form, citation_form = None, None

    return render_template(
        request, 'lexeme_extensions_edit.html',
        {"lexeme": lexeme,
         "domain": domain,
         "tagged_relations": tagged_relations,
         "action": action,
         "form": form,
         "citation_form": citation_form})


def add_lexeme_extension_citation(request, extension_id,
                                  domain=SemanticDomain.DEFAULT):
    """Given lexeme and semantic_extension, select source"""
    extension = SemanticExtension.objects.get(id=int(extension_id))

    def fix_form_fields(form):
        source_help_text = """Each source can only be cited once for each
                semantic extension.<br />If a source has already been cited the
                citation should be <a href="%s">edited</a> instead.
                """ % reverse("lexeme-domain-view",
                              args=[extension.lexeme.id, domain])
        # "disabled" attribute is not in general secure, but acceptable here
        # because we put it back in any case, even if the user manages to
        # change it illegally
        form.fields["extension"].widget.attrs["disabled"] = True
        form.fields["source"].help_text = source_help_text
        return form
    if request.method == "POST":
        post_data = dict((key, request.POST[key]) for key in request.POST)
        post_data["extension"] = extension_id
        form = fix_form_fields(SemanticExtensionCitationForm(post_data))
        # fix_form_fields(form)
        if "cancel" in form.data:
            return HttpResponseRedirect(
                reverse("lexeme-domain-view",
                        args=[extension.lexeme.id, domain]))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("lexeme-domain-view",
                        args=[extension.lexeme.id, domain]))
    else:
        form = fix_form_fields(SemanticExtensionCitationForm(
            initial={"extension": extension}))
        # fix_form_fields(form)
    return render_template(
        request, "extension_citation_add.html",
        {"extension": extension,
         "form": form})


def extension_citation_view(request, citation_id):
    citation = SemanticExtensionCitation.objects.get(id=int(citation_id))
    return render_template(
        request, "extension_citation_view.html",
        {"citation": citation})


def language_domain_view(request, language, domain=SemanticDomain.DEFAULT):
    try:
        language = Language.objects.get(ascii_name=language)
    except(Language.DoesNotExist):
        language = get_canonical_language(language)
        return HttpResponseRedirect(
            reverse("language-domain-view",
                    args=[language.ascii_name, domain]))
    try:
        relations = SemanticRelation.objects.filter(
                id__in=SemanticDomain.objects.get(name=domain).relation_id_list)
    except SemanticDomain.DoesNotExist:
        raise Http404("SemanticDomain '%s' does not exist" % domain)
    extensions = SemanticExtension.objects.filter(
            relation__in=relations,
            lexeme__language=language).order_by(
                "relation__relation_code",
                "lexeme__phon_form",
                "lexeme__source_form")

    # change language
    redirect, form = goto_language_domain_form(request, domain)
    form.fields["language"].initial = language.id
    if redirect:
        return redirect

    return render_template(
        request, 'language_domain_view.html',
        {"language": language,
         "domain": domain,
         "semantic_extensions": extensions,
         "form": form})


def language_domains_list(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except(Language.DoesNotExist):
        language = get_canonical_language(language)
        return HttpResponseRedirect(
            reverse("language-domains-list",
                    args=[language.ascii_name]))
    domain_ids = set(SemanticExtension.objects.filter(
            lexeme__language=language).values_list("relation_id", flat=True))
    domains = []
    for domain in SemanticDomain.objects.all():
        if set(domain.relation_id_list) & domain_ids:
            domains.append(domain)
    return render_template(
        request, 'language_domains_list.html',
        {"domains": domains, "language": language})


@login_required
def add_semantic_domain(request):
    if request.method == "POST":
        form = EditSemanticDomainForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse('view-domains'))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("edit-semantic-domain",
                        args=[form.cleaned_data["name"]]))
    else:
        form = EditSemanticDomainForm()
    return render_template(
        request, "semantic_domain_edit.html", {"form": form})


def goto_language_domain_form(request, domain):
    """Returns a tuple (redirect, form), only one of which is valid"""
    redirect = None
    if request.method == 'POST':
        form = ChooseLanguageForm(request.POST)
        if form.is_valid():
            language = form.cleaned_data["language"]
            redirect = HttpResponseRedirect(
                reverse("language-domain-view",
                        args=[language.ascii_name, domain]))
    else:
        form = ChooseLanguageForm()
    return (redirect, form)


def view_semantic_domain(request, domain):
    try:
        sd = SemanticDomain.objects.get(name=domain)
    except SemanticDomain.DoesNotExist:
        raise Http404("SemanticDomain '%s' does not exist" % domain)
    sr = SemanticRelation.objects.filter(id__in=sd.relation_id_list)
    redirect, form = goto_language_domain_form(request, domain)
    if redirect:
        return redirect
    return render_template(
        request, "semantic_domain_view.html",
        {"semantic_domain": sd, "relations": sr, "form": form})


@login_required
def edit_semantic_domain(request, domain=SemanticDomain.DEFAULT):
    sd = SemanticDomain.objects.get(name=domain)
    if request.method == "POST":
        name_form = EditSemanticDomainForm(request.POST, instance=sd)
        items_form = ChooseSemanticRelationsForm(request.POST)
        items_form.fields["included_relations"].queryset = \
            SemanticRelation.objects.filter(id__in=sd.relation_id_list)
        items_form.fields["excluded_relations"].queryset = \
            SemanticRelation.objects.exclude(id__in=sd.relation_id_list)
        if items_form.is_valid() and name_form.is_valid():
            exclude = items_form.cleaned_data["excluded_relations"]
            include = items_form.cleaned_data["included_relations"]
            new_list = sd.relation_id_list
            if include:
                new_list.remove(include.id)
            if exclude:
                new_list.append(exclude.id)
            sd.relation_id_list = new_list
            sd.save()
            name_form.save()
            if "cancel" in request.POST:
                return HttpResponseRedirect(reverse("view-domains"))
            else:
                return HttpResponseRedirect(
                    reverse("edit-semantic-domain", args=[sd.name]))
        else:
            assert False, "Shouldn't get to here"
    else:
        name_form = EditSemanticDomainForm(instance=sd)
        items_form = ChooseSemanticRelationsForm()
        items_form.fields["included_relations"].queryset = \
            SemanticRelation.objects.filter(id__in=sd.relation_id_list)
        items_form.fields["excluded_relations"].queryset = \
            SemanticRelation.objects.exclude(id__in=sd.relation_id_list)
    return render_template(
        request, "semantic_domain_change_items.html",
        {"items_form": items_form,
         "name_form": name_form,
         "semantic_domain": sd})


def confirm_delete_context(request, domain):
    return RequestContext(request, {"domain_name": domain})


@login_required
@confirm_required("confirm_delete.html", confirm_delete_context)
def delete_semantic_domain(request, domain):
    sd = SemanticDomain.objects.get(name=domain)
    sd.delete()
    messages.warning(request, "Semantic domain '%s' deleted" % domain)
    return HttpResponseRedirect(reverse("view-domains"))
