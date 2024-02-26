FROM python:3.11.6
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE 1
ENV TZ="Australia/Perth"
RUN wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo tee /etc/apt/trusted.gpg.d/pgdg.asc &>/dev/null
RUN echo "Installing System Utils." && apt-get update && apt-get install -y \
    -o Acquire::Retries=4 --no-install-recommends \
    # Sys Utils
    openssh-client rsync vim ncdu wget systemctl \
    # Postgres
    postgresql postgresql-client 

WORKDIR /usr/src/app
RUN pip install --upgrade pip
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -
ENV PATH="${PATH}:/etc/poetry/bin"

COPY . ./backend
WORKDIR /usr/src/app/backend

# Add the alias commands and configure the bash file
RUN echo '# Custom .bashrc modifications\n' \
    'fromdate="03.04.2023"\n' \
    'todate=$date\n' \
    'from=`echo $fromdate | awk  -F\. '\''{print $3$2$1}'\''`\n' \
    'to=`echo $todate | awk  -F\. '\''{print $3$2$1}'\''`\n' \
    'START_DATE=`date --date=$from +"%s"`\n' \
    'END_DATE=`date --date=$to +"%s"`\n' \
    'DAYS=$((($END_DATE - $START_DATE  ) / 86400 ))\n' \
    'RED='\''\033[0;31m'\''\n' \
    'GREEN='\''\033[0;32m'\''\n' \
    'PURPLE='\''\033[0;35m'\''\n' \
    'BLUEBG='\''\033[0;44m'\''\n' \
    'ORDBG='\''\033[0;48m'\''\n' \
    'GREENBG='\''\033[0;42m'\''\n' \
    'NC='\''\033[0m'\'' # No Color\n' \
    'LB='\''\e[94m'\'' #Light Blue\n' \
    'PS1="\n\n\[$(tput sgr0)\]\[\033[38;5;105m\]\d\[$(tput sgr0)\], \[$(tput sgr0)\]\[\033[38;5;15m\]\D{%H:%M:%S}\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;76m\]\w\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;10m\]--------------------------------\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;14m\]>\[$(tput sgr0)\]"\n' \
    'alias home="cd ~"\n' \
    'alias settz="export TZ=$TZ"\n' \
    'alias edit="home && vim .bashrc"\n' \
    'alias cleardb="python manage.py sqlflush | python manage.py dbshell"\n' \
    'alias migrate="python manage.py makemigrations && python manage.py migrate"\n' \
    'alias dump_prod="PGPASSWORD=$PRODUCTION_PASSWORD pg_dump -h $PRODUCTION_HOST -d $PRODUCTION_DB_NAME -U $PRODUCTION_USERNAME -f prod_dump.sql"\n' \
    'alias res_prod="PGPASSWORD=$PRODUCTION_PASSWORD psql -h $PRODUCTION_HOST -d $PRODUCTION_DB_NAME -U $PRODUCTION_USERNAME -a -f prod_dump.sql"\n' \
    'alias dump_uat="PGPASSWORD=$UAT_PASSWORD pg_dump -h $PRODUCTION_HOST -d $UAT_DB_NAME -U $UAT_USERNAME -f uat_dump.sql"\n' \
    'alias res_uat="PGPASSWORD=$UAT_PASSWORD psql -h $PRODUCTION_HOST -d $UAT_DB_NAME -U $UAT_USERNAME -a -f uat_dump.sql"\n' \
    'alias dump_old="PGPASSWORD=$OLD_PASSWORD pg_dump -h $OLD_HOST -d $OLD_DB_NAME -U $OLD_USERNAME -f old_dump.sql"\n' \
    'alias res_old="PGPASSWORD=$OLD_PASSWORD psql -h $OLD_HOST -d $OLD_DB_NAME -U $OLD_USERNAME -a -f old_dump.sql"\n' \
    'alias connectprod="PGPASSWORD=$PRODUCTION_PASSWORD psql -h $PRODUCTION_HOST -d $PRODUCTION_DB_NAME -U $PRODUCTION_USERNAME"\n' \
    'alias connectuat="PGPASSWORD=$UAT_PASSWORD psql -h $PRODUCTION_HOST -d $UAT_DB_NAME -U $UAT_USERNAME"\n' \
    'alias connectold="PGPASSWORD=$OLD_PASSWORD psql -h $OLD_HOST -d $OLD_DB_NAME -U $OLD_USERNAME"\n' \
    'settz\n'>> ~/.bashrc

RUN poetry config virtualenvs.create false
# RUN echo -e "3.12" | poetry init
RUN poetry init
# Necessary to fix pandas/numpy installation issues on 3.12 with poetry
RUN sed -i 's/python = "^3.11"/python = "<3.13,>=3.10"/' pyproject.toml

# Base
RUN poetry add brotli dj-database-url django-cors-headers django-environ \
    djangorestframework django psycopg2-binary python-dotenv python-dateutil \
    requests whitenoise[brotli] gunicorn pandas \
    beautifulsoup4 sentry-sdk[django] weasyprint

RUN poetry add pillow
RUN poetry add html2text


EXPOSE 8000
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000"]