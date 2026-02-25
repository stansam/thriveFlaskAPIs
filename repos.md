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
