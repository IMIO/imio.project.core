/srv/archgenxml/agx27/bin/archgenxml --cfg agx.conf imioprojectcore.zargo
#manage generated.pot
#cp temp/i18n/generated.pot ../locales/agx.pot

#copying workflows
#cp temp/profiles/default/workflows.xml ../profiles/default
cp -r temp/profiles/default/workflows ../profiles/default

#change the workflow name
sed -i 's/title=\"project_workflow\"/title=\"Project workflow\"/g' ../profiles/default/workflows/project_workflow/definition.xml

