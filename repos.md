Starting with the base and user repository(db queries and crud ops) level workflows from

repository-workflows.md
, implement the robust production ready exhaustive class based repository level functions. For modularity and flexibility store the seperate repository workflows inside "app/services/" and each in it's own seperate folders, every folder should have **init**.py files setup. Also create reusable utils in each workflow folder to avoid redundancy and simplify the code. Maintain strict code standards, security and best practices. Where placeholders are to be implemented leave TODO comments and also create a TODO document in the specific workflow folder, so that each workflow has it;s own TODO files. AVOID placeholders or incomplete functionalities unless no toher option is present and document accordingly. Create an implementation plan for review before writing any code.

Now, proceed with the full auth and user service level workflows from @beautifulMention.

implement the robust production ready exhaustive class based service level functions. For modularity and flexibility store the seperate service workflows inside "app/services/" and each in it's own seperate folders, every folder should have **init**.py files setup. Also create reusable utils in each workflow folder to avoid redundancy and simplify the code. Also create a "app/dto" folder for holding all the service workflow strict DTOs(confirm required and optional fields and their types by referencing the relevant backed model) where each workflow DTOs are in their seperate folders for modularity, security and flexibilty Maintain strict code standards, security and best practices. Where placeholders are to be implemented leave TODO comments and also create a TODO document in the specific workflow folder, so that each workflow has it;s own TODO files. AVOID placeholders or incomplete functionalities unless no toher option is present and document accordingly. Create an implementation plan for review before writing any code.

I want you to read

context.md
carefully and in full to understand what I am working on.Then analyse each and every one of the files inside the following folders listed below, (Also read files inside the subfolders within them) by first listing all the files within that folder and it's subfolders, confirming total file count then reading each and every file, countercheck read-files completion by referring to the total file count. Here are the folders for indepth recursive analysis:

1. Models :

models

2. Repositories:

repository

3. Services

services

4. DTOs

dto

These respectively hold the models, repository level functions, service-level functions, and dtos.

Generate two comprehensive and detailed seperate reports one for the implemented repository level functionality and the other for the implemented service level functionality. Report on correctness, errors, mistakes, improvements, security, production readiness, future expansion and suitabilty with the requirements specifications.

Before any analysis generate an implementation plan for review, detailing how you will carry out the in depth analysis.

I want you to read @beautifulMention
carefully and in full to understand what I am working on.Then analyse each and every one of the files inside the following folders listed below, (Also read files inside the subfolders within them) by first listing all the files within that folder and it's subfolders, confirming total file count then reading each and every file, countercheck read-files completion by referring to the total file count. Here are the folders for indepth recursive analysis:

1. Models : @beautifulMention
2. Repositories: @beautifulMention
3. Services: @beautifulMention
4. DTOs: @beautifulMention
5. Auth Bp - @beautifulMention
6. Admin BP - @beautifulMention
7. Client Bp - @beautifulMention
8. Main Bp - @beautifulMention
9. Utils @beautifulMention
10. Email Templates @beautifulMention
11. Sockets @beautifulMention

These respectively hold the models, repository level functions, service-level functions, dtos, auth blueprint, admin blueprint, client blueprint, main blueprint, utils folder, email templates folder and sockets folder.
Also implemented is a celery_worker @beautifulMention
After thorough analysis and full comprehension of current codebase state, it's scope and general project knowledge is firmly grasped carefully analyse this completion plan,@beautifulMentionand generate two comprehensive and detailed seperate reports one for the codebase implementation state and the correctness of the current completion plan and the other report a TRUE detailed project backend completion plan from all that you have gathered so far. Report on correctness, errors, mistakes, improvements, security, production readiness, future expansion and suitabilty with the requirements specifications.

Before any analysis generate an implementation plan for review, detailing how you will carry out the in depth analysis.

As a senior backend developer, carefully and critically read and analyse the phase 1 implementation steps in

TRUE_Backend_Completion_Plan.md
, conservatively approach each step in this phase indivivually and explore it's domain and context wholly, also perform a vigourous and thorough reanalysis of each of the phase step's codebase dependencies, imports and any dependent functionality and implement it fully or document in the TODOs if scope is too large, but generally avoid placeholders or incomplete functionality if possible. In short treat each step in a phase as an entire domain to be carefully thought through before proceeding, this is where your years of experience helps.

Ensure strict codeing standards and COMPLETE implementation THROUGHOUT.

Generate comprehensive detailed implementation plan after deep thinking and vigorous analysis for review before writing any code.
