UPDATE ik_screen_field
SET widget_parameters = REPLACE(widget_parameters, 'dialogMessage', 'content')
WHERE widget_parameters ILIKE '%dialogMessage%';

UPDATE ik_screen_field
SET widget_parameters = REPLACE(widget_parameters, 'dialogContent', 'content')
WHERE widget_parameters ILIKE '%dialogContent%';

UPDATE ik_screen_field
SET widget_parameters = REPLACE(widget_parameters, 'dialogBeforeDisplayEvent', 'beforeDisplayEvent')
WHERE widget_parameters ILIKE '%dialogBeforeDisplayEvent%';

UPDATE ik_screen_field
SET widget_parameters = REPLACE(widget_parameters, 'dialogName', 'name')
WHERE widget_parameters ILIKE '%dialogName%';

UPDATE ik_screen_field
SET widget_parameters = REPLACE(widget_parameters, 'dialogTitle', 'title')
WHERE widget_parameters ILIKE '%dialogTitle%';

UPDATE ik_screen_field
SET widget_parameters = REPLACE(widget_parameters, 'continueNm', 'continueName')
WHERE widget_parameters ILIKE '%continueNm%';

UPDATE ik_screen_field
SET widget_parameters = REPLACE(widget_parameters, 'cancelNm', 'cancelName')
WHERE widget_parameters ILIKE '%cancelNm%';