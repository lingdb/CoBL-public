# -*- coding: utf-8 -*-
from wtforms import BooleanField


class WTFormToFormgroup():
    fieldsWithLabel = []  # :: [(fieldName, kwargs)]
    fieldsWithoutLabel = []  # :: [(fieldName, kwargs)]

    def renderAsFormGroup(self):
        hiddenFields = []
        for fieldName, kwargs in self.fieldsWithoutLabel:
            field = getattr(self, fieldName)
            hiddenFields.append(field(**kwargs))

        visibleFields = []
        for fieldName, kwargs in self.fieldsWithLabel:
            field = getattr(self, fieldName)
            if isinstance(field, BooleanField):
                visibleFields.append(self._buildCheckboxField(field, **kwargs))
                pass
            else:
                visibleFields.append(self._buildLabelField(field, **kwargs))

        return ''.join(hiddenFields) + ''.join(visibleFields)

    def _buildCheckboxField(self, field, **kwargs):
        formatGroup = \
            '<div class="form-group">' \
            '<div class="col-sm-offset-4 col-sm-8">' \
            '<div class="checkbox">' \
            '<label>%s%s</label>' \
            '</div>' \
            '</div>' \
            '</div>'
        return formatGroup % (field(**kwargs), field.label)

    def _buildLabelField(self, field, **kwargs):
        formatGroup = \
            '<div class="form-group">' \
            '<label for="" class="col-sm-4 control-label">%s</label>' \
            '<div class="col-sm-8">%s</div>' \
            '</div>'
        return formatGroup % (field.label, field(**kwargs))
