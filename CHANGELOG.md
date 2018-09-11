Changelog

- 2.1.x
  - Aristotle MDR core
    - Fixed bug where Workgroups showed incorrectly in dropdowns #901
    - Fixed bug where users of IE and Edge couldn't properly use select2 dropdowns #894
    - Removed all Channels code, fixes #885. We have no reports of this in use and will replace with Celery later.
    - Added help for new search tokens #887 that covers status and identifier search
    - Fix for dataset order display and reordering
    - Update logout redirect to home with a message
    - Increase text lenght for submitting organisation and responsible organisation fields
    - Efficiency impovements on list pages
    - Dependancy updates

- 2.1.3
    - Identifier and Namespace searching
    - Fix for api list bug

- 2.1.2
    - Fixed editor UI Bug
    - Improved logging of config errors

- 2.1.1
    - Fix to signup email url generation to ensure domain is in invite email
    - Ensure invited users are given a valid password to ensure recovery can occur
    - Fix to workgroup member list to improve efficiency of workgroup member page
    - Pin django-filters dependancy

- 2.1.0
    - Changed how root URL `aristotle.example.com/` resolves: for anonymous users it redirects to `aristotle.example.com/home`, for logged in users it redirects to `aristotle.example.com/account/home/`
    - Removed official support for Windows & MSSQL
    - Simplified configuration for testing
    - Ability to order Data Elements within Data Element Derivations
    - Ability to order Slots and Identifiers
    - Slots now have permissions (Public, Private, Workgroup)
    - Removal of short name
    - Minor design of Metadata InfoBox when showing last updating user
    - Fix glossary migrations
    - Added a user profile page
    - Option allowing users to self signup to a registry
    - Removal of short_name
    - Registration Authorities can now be retired

    - UI
      - Improved notifications loading
    
    - API changes
      - Rest API token authentication

- 2.0.0
    - **Dependency notes:**
      - Dropped support for Python 3.4 and below, and Django 1.10 and below
      - Dropped requirements for `django-bootstrap3-datetimepicker-2`
      - Dependancies are now defined using `Pipfile` instead of `setup.py` and `requirements.txt`
      - Moved to a single monorepo that holds the core code and all Aristotle Metadata Extensions
    - Fixed WCAG testing and corrected some minor accessibility issues - #697
    - Minor tweak to dash board - 'recent workgroups' panel no longer exists, 'recent favourites' is no above 'recent actions'
    - Darkend Bootstrap "brand-danger" variable by 10% to improve contrast
    - Speed improvements on search pages - #715
    - Added links to Conceptual Domain to Value Domain page #766
    - Hide relationships section when no links are on a metadata item
    - Allow Permissible Values of any length
    - All "Aristotle Components" (including Permissible and Supplementary Values) can be edited and reordered from their parent object edit screen
    - Permissible Values lists now only show value meaning dropdowns when the Value Domain has an attached Conceptual Domain #756
    - Value Meaning start and end dates are now shown on Value Domain and Conceptual Domain pages
    - Fixed bug where spaces in search facets showed blank pages
    - Search facet links now return to the first page to prevent 404s #763
    - Items can now be deleted from the sandbox
    - Added review page for any status changes
    - Fixed Data Element Wizard incorrectly stating it was creating a "Data Element Concept"
    - Fixed issue where cached permissions would check against the wrong item type

- 1.6.5
  - Fixed regression where private methods showed up in creation wizards
  - Fixed error with wizards fialing if search engine is stale, #736
  - Fixed many-to-many fields not saving when creating items, #732
  - Gave Aristotle links a unified namespace (`aristotle_mdr_links`)
  - Creation list now displays apps in alphabetical order, #740
  - Cloned items now save the submitter, preventing forbidden page errors for submitters if there is no workgroup attached
  - Cloning an item now only required view permissions, not edit permissions
  - Fixed dashboard sidebar display in Internet Explorer 11

- 1.6.4
  - Fixed error when bulk endorsing content #728
  - Fixed spelling error on 403 page
  - Fixed regression where items with no workgroup couldn't be bulk moved to a workgroup #734
  - Fixed bug where "add user" link wouldn't work in workgroup member pages #731
  - Fixed display of paginator bar for small page numbers #714
  - Removed un-editable fields from creation wizards
  - Corrected spelling error in DE and DEC wizards

- 1.6.3
  - Fixed bug when registration form didn't show username errors
  - Improved how invitation emails are rendered
  - Fix bug in registation authority list
  - Removed dead link in user page, fixed user list generation #727
  - Fix regression when searching for help

- 1.6.2
  - Re-release of 1.6.1 due to upload error with PyPI

- 1.6.1
    - **Dependency note:** Version 1.6.0 will be the last minor version of Aristotle to support Python 2 and Django 1.8
      The next version of Aristotle will be version 2 and will require:
        - Python 3.5 or above
        - Django 1.11 or above
    - Removed incorrect instructions on login page
    - Improved disabling of metadata extensions in code/configuration.
        This allows for more dynamic loading of extensions and APIs at runtime
    - Improved bulk action handling when performing an action with "select all"
        by adding cached querysets - fixes #685 by implementing #543
    - Changes to dropdown menu list items in the the default theme to improve accessibility checks
    - Javascript fixes to ensure rich text and relation editors load correctly (Thanks @rafen)
    - Fixed workgroup pagination filter label to connect to search box
    - New workgroup creation and list pages
    - Fixed a bug where search results where showing HTML entities - see #707 (Thanks @rafen)
    - Workgroup users now properly informed when accessing a workgroup they arent a member of (Thanks @DeKan)
    - Footer is now sticky by default
    - Metadata statistics pages now use browse pages links
    - Added a new user management section to the Aristotle Dashboard
    - Visual enhancements to item revision comparison page
    - Added change stats and view history options to the action menu
    - Removed link to django admin item history
    - **Permissions change** Permissions on who can see registry members has changed to support better collaboration between users. Workgroup managers and Registration Authority Managers are now assumed to be trusted users, and can now search for users to add to their respective groups.
    - **Configuration change:**
        - new options - ``ARISTOTLE_SETTINGS_STRICT_MODE``, if False errors in ARISTOTLE_SETTINGS will be logged and not prevent the app from working. Defaults to True.
        - ``BULK_ACTION`` option will no longer cause critical isuses if incorrectly configured. Errors can be logged instead
        - ``CONTENT_EXTENSIONS`` option will no longer cause critical isuses if incorrectly configured. Errors can be logged instead
        - ``DOWNLOADERS`` option will not cause critical isuses if incorrectly configured. Errors can be logged instead
        - ``USER_VISIBILITY`` option allows for broader visibility of users when creating groups, and gives managers workgroup and registration authority managers results based on partial matches. This can be set to "owners" only to revert to original functionality.
    - **Breaking change:** Download options have been moved into the ``ARISTOTLE_SETTINGS``
        under the ``DOWNLOADERS`` key
    - **Breaking change:** The Aristotle setting ``BULK_ACTION`` is now a list of python module strings. Update to 1.6.0 by removing keys and keeping the list of associated values
    - **Breaking change:** The PDF download library is no longer included by default,
        and must be installed from github - https://github.com/aristotle-mdr/aristotle-pdf-downloads
    - **Breaking change:** Contrib URLs are no longer loaded automatically. Contrib apps now need
        to have URLs loaded manually in a project urls.py
    - **Breaking change:** Removed the ``clone`` and ``adminLink`` template tags, performing these actions via the django admin pages
        will be deprecated in future versions
    - Fixed regression where help pages with no app label were hidden in listings
    - Fixed regression where help pages were not searchable

- 1.6.0
  - Unreleased due to UUID bug

- 1.5.7
    - Pinned bootstrap-timepicker-datepicker version

- 1.5.6
    - Fixed search indexes for Value Domains and Conceptual Domains #676
    - Fixed search page html bug #673
    - Added improved search indexes for Units of Measure & Data Element Derivations
    - Fixed bug around search indexes not populaitng properly if a search index template didn't exist

- 1.5.5
    - Added Many to Many fields to generic.views.GenericAlterOneToManyView
    - Added Date Widget to Date time fields

- 1.5.4
    - Fixes for review requests:
        - Fixed hints on visibiity changes, #664
        - Minor CSS improvements
        - Matched wording around cascade registration to match status changes
        - Fixed bug where review request popover windows wouldn't work, #663
        - Fixed bug where bulk review requests would fail, #662
        - Correct how sandbox shows cancelled reviews, #660
    - Add new URL for accessing items via their UUID
    - Change relation fields for concepts to support more intelligent GraphQL querying
    - UI improvements to lists of items

- 1.5.3
    - Added generic delete confirmation view
    - Conceptual Domains improvements:
        - Added value meaning editor, and admin inline editor
        - Improved layout and display of Conceptual Domains
        - Improved search index for Conceptual Domains
    - Improved search index for Value Domains
    - Allow arity of relationships to be blank #652
    - Improved how value domains are compared using the comparator #655
    - Removed UUIDs from comparator #655
    - Fix display bug that incorecctly stated how visibility of items would change #648  
    - Fix bug that listed unregistered metadata in downloads #659

- 1.5.2
    - Autocompletes now restrict via UUID
    - Added `serialize_weak_entities` to ValueDomain and ConceptualDomain allow for codes to be transmitted via API
    - Fix slots in PDFs #635

- 1.5.1
    - Fixed UUID4 transcription error in migrations #625
    - Users can search for all content, not just their own - #626
    - Changelog added
