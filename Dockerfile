# ====================== IMAGE & CONFIG ======================
# Use the local version that works with poetry config when testing in dev (3.12.3)
FROM python:3.12.3
# Ensures Python output sent to terminal for logging
ENV PYTHONUNBUFFERED=1
# Prevent additional .pyc files on disk
ENV PYTHONDONTWRITEBYTECODE 1
# Set timezone to Perth for logging
ENV TZ="Australia/Perth"

# ====================== OS LEVEL DEPENDENCIES ======================
# POSTGRES REQUIRED FOR MIGRATION SCRIPT / PERFORMING SQL ACTIONS AND CUSTOM COMMANDS - Commented out
# RUN wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo tee /etc/apt/trusted.gpg.d/pgdg.asc &>/dev/null
RUN echo "Installing System Utils." && apt-get update && apt-get install -y \
    -o Acquire::Retries=4 --no-install-recommends \
    # Sys Utils
    vim wget ncdu systemctl
# Sys Utils with Postgres
# vim wget ncdu systemctl \
# postgresql postgresql-client 

# Set working dir of project
WORKDIR /usr/src/app

# Install Poetry
RUN pip install --upgrade pip
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -
ENV PATH="${PATH}:/etc/poetry/bin"

# Prince Download
RUN echo "Downloading Prince Package" \
    && DEB_FILE=prince.deb \
    && wget -O ${DEB_FILE} \
    https://www.princexml.com/download/prince_15.3-1_debian12_amd64.deb
# Prince installer
RUN apt-get update && apt-get install -y -o Acquire::Retries=4 --no-install-recommends \
    gdebi
# Prince Install
RUN echo "Installing Prince stuff" \
    && DEB_FILE=prince.deb \
    && yes | gdebi ${DEB_FILE}  \
    && echo "Cleaning up" \
    && rm -f ${DEB_FILE}
# Prince ENV 
ENV PATH="${PATH}:/usr/lib/prince/bin"

# ====================== DEV FILES AND DEPENDENCIES ======================

# Move local files over
COPY . ./backend
WORKDIR /usr/src/app/backend

# Configure Poetry to not use virtualenv
RUN poetry config virtualenvs.create false
# Install deps from poetry lock file made in dev
RUN poetry install 

# ====================== USER & PERMISSIONS ======================
# # Create Non-root: assign build time vars UID and GID to same value 10001
# ARG UID=10001
# ARG GID=10001
# # Create Non-root: use vars to create group and user assigned to it, 
# # without home or log files
# RUN groupadd -g "${GID}" spmsuser \
#     && useradd --create-home --home-dir /home/spmsuser --no-log-init --uid "${UID}" --gid "${GID}" spmsuser

# Add the alias commands and configure the bash file
RUN echo '# Custom .bashrc modifications\n' \
    'fromdate="21.06.2024"\n' \
    'todate=$date\n' \
    'from=`echo $fromdate | awk -F\. '\''{print $3$2$1}'\''`\n' \
    'to=`echo $todate | awk -F\. '\''{print $3$2$1}'\''`\n' \
    'START_DATE=`date --date=$from +"%s"`\n' \
    'END_DATE=`date --date=$to +"%s"`\n' \
    'DAYS=$((($END_DATE - $START_DATE) / 86400 ))\n' \
    'RED='\''\033[0;31m'\''\n' \
    'GREEN='\''\033[0;32m'\''\n' \
    'PURPLE='\''\033[0;35m'\''\n' \
    'BLUEBG='\''\033[0;44m'\''\n' \
    'ORDBG='\''\033[0;48m'\''\n' \
    'GREENBG='\''\033[0;42m'\''\n' \
    'NC='\''\033[0m'\'' # No Color\n' \
    'LB='\''\e[94m'\'' # Light Blue\n' \
    'PS1="\n\n\[$(tput sgr0)\]\[\033[38;5;105m\]\d\[$(tput sgr0)\], \[$(tput sgr0)\]\[\033[38;5;15m\]\D{%H:%M:%S}\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;76m\]\w\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;10m\]--------------------------------\[$(tput sgr0)\]\n\[$(tput sgr0)\]\[\033[38;5;14m\]>\[$(tput sgr0)\]"\n' \
    'alias home="cd ~"\n' \
    'alias settz="export TZ=$TZ"\n' \
    'alias edit="home && vim .bashrc"\n' \
    'alias cleardb="python manage.py sqlflush | python manage.py dbshell"\n' \
    'alias migrate="python manage.py makemigrations && python manage.py migrate"\n' \
    'settz\n' >> ~/.bashrc


#  'alias connect_prod='"'"'eval $(echo $DB_URL | awk -F[/:@] '\''{print "USER="$4" PASSWORD="$5" HOST="$6" NAME="$7}'\'') && PGPASSWORD=$PASSWORD psql -h $HOST -d $NAME -U $USER'"'"'\n' \
#     'alias dump_prod='"'"'eval $(echo $DB_URL | awk -F[/:@] '\''{print "USER="$4" PASSWORD="$5" HOST="$6" NAME="$7}'\'') && PGPASSWORD=$PASSWORD pg_dump -h $HOST -d $NAME -U $USER -f -Fc database_dump.sql'"'"'\n' \
#     'alias res_prod='"'"'eval $(echo $DB_URL | awk -F[/:@] '\''{print "USER="$4" PASSWORD="$5" HOST="$6" NAME="$7}'\'') && PGPASSWORD=$PASSWORD psql -h $HOST -d $NAME -U $USER -a -f database_dump.sql'"'"'\n' \

# >> /home/spmsuser/.bashrc
# >> ~/.bashrc
#     >> /home/spmsuser/.bashrc

# # Ensure bashrc belongs to correct user and runs
# RUN chown ${UID}:${GID} /home/spmsuser/.bashrc
# # Own app
# RUN chown -R ${UID}:${GID} /usr/src/app
# # Own the license file to update it
# RUN chown -R ${UID}:${GID} /usr/lib/prince/license

# Ownership of files etc. is set in init container
# chown -R ${UID}:${GID} /usr/src/app/backend/files

# # Ensure entrypoint script can run for prince license and gunicorn
RUN chmod +x /usr/src/app/backend/entrypoint.sh
# # Switch to non-root user
# USER ${UID}

# ====================== HEALTH CHECK ======================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health/ || exit 1

# ====================== LAUNCH ======================
# Expose and enter entry point (launch django app on p 8000)
EXPOSE 8000
# Set entrypoint
ENTRYPOINT ["/usr/src/app/backend/entrypoint.sh"]