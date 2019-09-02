Changelog
=========

1.3 (unreleased)
----------------

- Add budget.behavior
  [vpiret]

- Corrected persistency bug in annotation when removing item.
  Don't set children budget at all on initial state.
  Removed all sub children on initial state.
  [sgeulette]
- Managed move event to update children budget annotation
  [sgeulette]

1.2 (2019-06-23)
----------------

- Use collapsible view.
  [sgeulette]
- Changed list requirement validator
  [sgeulette]
- Do not consider deactivated contact in vocabularies
  [sgeulette]
- Can hide reference number
  [sgeulette]

1.1 (2019-01-15)
----------------

- Added budget possible years on projectspace.
  [sgeulette]
- Added viewlet for annexes
  [fngaha]
- Do not consider deactivated contact in vocabularies
  [sgeulette]

1.0 (2016-12-08)
----------------
- Replace collective.z3cform.rolefield by dexterity.localrolesfield
  [cmessiant]
- Some fixes
  [cmessiant]
- Removed default dates
  [sgeulette]
- Use now imio.helpers container view
  [sgeulette]
- Some cleaning
  [sgeulette]

0.3 (2014-12-11)
----------------
-

0.2 (2013-11-19)
----------------
- Turned budget rich text field into a DataGridField + rich text field for budget comments
- Optimized RemovedValueIsNotUsedByXXXFieldValidator to work with DataGridFields
- Avoid performances problems
- Added "observation" to manage "prior observations"

0.1 (2013-08-01)
----------------
- Initial release.
  [s.geulette@imio.be]
