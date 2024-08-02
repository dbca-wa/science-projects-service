Place your data in this folder under a subdirectory "legacy_data". It will be gitignored.

THE FOLLOWING IS FROM THE SCIENCE.DBCA.WA.GOV.AU README:
= README
:scinet: Science Internet
:sww: Science Website Workbench

The primary feature of the {sww} and {scinet} applications is providing staff with a way to edit their professional profile and publish this online.

The _main_ goals of this are to:

-   provide the public with a way to contact research staff,

-   make it easy to determine who might be best to contact, based on staff keywords and research expertise,

Some _additional_ goals of this are to:

-   avoid publishing personal information,

-   with the help of the soft delete feature, make it possible to hide a staff profile if necessary.

== Tables

=== Staff

[%header,cols="1,1,3"]
|===
| Name | Full Name | Notes
| `id` | Identifier | The row's unique identifier and the table's primary key. A value between `1` and `65535`.
| `aucode` | Author Code | The unique identifier for this staff member in the Library's staff bibliography dataset. Effectively a foreign key.
| `corporate_user_id` | Corporate Identifier | The unique identifier for this staff member in the Department's systems, usually the part of the email address before the `@` symbol. Effectively a foreign key.
| `centreid` | Centre Identifier | The unique identifier for this staff member's most common office location. The foreign key to `centres.id`.
| `title` | Title | This staff member's formal title.
| `givenname` | Given Name | This staff member's personal name without the surname.
| `midinitial`| Middle Initials | This staff member's middle initials, e.g. `A.E.`
| `surname` | Surname | This staff member's family name.
| `namedir` | Name Direction | The country code, e.g. `en`, for how this person's name should be presented. For most european names this is surname-last, but some countries use surname-first. This value helps code decide which way to present the name.
| `directphone` | Direct Phone Number | This staff member's direct phone number.
| `directfax` | Direct Facsimile Number | This staff member's direct fax number.
| `email` | Email Address | This staff member's email address.
| `profile` | Profile Text | The text of the profile part of this staff member's professional profile.
| `expertise` | Expertise Text | The text of the expertise part of this staff member's professional profile.
| `cv` | CV Text | The text of the curriculum vitae part of this staff member's professional profile.
| `projects` | Projects Text | The text of the projects part of this staff member's professional profile.
| `publications` | Publications Text | The text of the publications part of this staff member's professional profile.
| `updated` | Updated On | The date and time to the second in Perth's time zone on which this profile was last updated.
| `hidden` | Hidden | Whether this staff profile has been hidden from view (aka "soft deleted").
|===

=== Staff Keywords

[%header,cols="1,1,3"]
|===
| Name | Full Name | Notes
| `id` | Identifier | The row's unique identifier and the table's primary key. A value between `1` and `65535`.
| `staffid` | Staff Member Identifier | Foreign key to `staff.id`.
| `keyword` | Keyword | A single keyword for this staff member.
|===

=== Centres

[%header,cols="1,1,3"]
|===
| `id` | Identifier | This centre's unique identifier. A value between `1` and `65535`.
| `name` | Centre Name | The centre's full name.
| `mail_street` | Street of mailing address |
| `mail_suburb` | Suburb of mailing address |
| `mail_state` | State of mailing address |
| `mail_postcode` | Postcode of mailing address |
| `mail_country` | Country of mailing address |
| `strt_street` | Street of street address |
| `strt_suburb` | Suburb of street address |
| `strt_state` | State of street address |
| `strt_postcode` | Postcode of street address |
| `strt_country` | Country of street address |
| `phone` | Centre Phone | The centre's phone number, usually to a secretary or personal assistant.
| `fax` | Centre Facsimile | The centre's fax number, usually (formerly?) managed by a secretary or personal assistant.
|===
