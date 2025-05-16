The demonstration how to use sqlalchemy ORM.
Basic tutorial, ORM concepts: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#synopsis-orm

The example demonstrates how to organize a simple project with the database using.  

## ORM using

[Tutorial sources are here](https://alembic.sqlalchemy.org/en/latest/tutorial.html#creating-an-environment)

Steps to use ORM in a project:  
1. Init alembic in the root of the directory:  
   ```bash
   alembic init alembic
   ```
2. Fill `sqlalchemy.url` in file *alembic/alembic.ini* as URL to connect to the database.  
Examples:  
`sqlite+aiosqlite://~/tmp/db.sqlite3`,  
`postgresql+asyncpg://nick:password123@localhost/database123`,  
`mysql+asyncmy://nick:password123@localhost/database123`.  
Though, it is better to set it via environment variables.
3. Create a python module with models. [See example](https://docs.sqlalchemy.org/en/20/orm/quickstart.html#declare-models)
4. For using alembic, need to set `target_metadata = Base.metadata` in the file *alembic/env.py*.    
   `Base` is imported from the newly created module from the last step.

#### Create migration
```bash
alembic revision --autogenerate -m "Name of migration"
```

#### Update database with the last migration
```bash
alembic upgrade head
```
