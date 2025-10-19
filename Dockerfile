# syntax=docker/dockerfile:1

ARG APP_ENV=development
ARG ENABLE_XDEBUG=false

FROM php:8.3-cli AS builder
ARG APP_ENV=development

WORKDIR /app

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        unzip \
        libicu-dev \
        libzip-dev \
        libpng-dev \
        libjpeg62-turbo-dev \
        libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j"$(nproc)" \
        gd \
        intl \
        mysqli \
        pdo_mysql \
        zip

COPY composer.json composer.lock ./

RUN set -eux; \
    if [ "${APP_ENV}" = "production" ]; then \
        composer install --no-dev --classmap-authoritative --no-interaction --prefer-dist --optimize-autoloader; \
    else \
        composer install --no-interaction; \
    fi

################################################################################
# Runtime stage
################################################################################

FROM php:8.3-fpm-alpine AS runtime
ARG APP_ENV=development
ARG ENABLE_XDEBUG=false

ENV APP_ENV="${APP_ENV}"

WORKDIR /var/www/html

# Install runtime dependencies and PHP extensions
RUN set -eux; \
    apk add --no-cache \
        icu-data-full \
        icu-libs \
        libzip \
        libpng \
        libjpeg-turbo \
        freetype \
        tzdata; \
    apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS \
        icu-dev \
        libzip-dev \
        libpng-dev \
        libjpeg-turbo-dev \
        freetype-dev; \
    docker-php-ext-configure gd --with-freetype --with-jpeg; \
    docker-php-ext-install -j"$(nproc)" \
        gd \
        intl \
        mysqli \
        pdo_mysql \
        zip; \
    if [ "${ENABLE_XDEBUG}" = "true" ]; then \
        pecl install xdebug \
        && docker-php-ext-enable xdebug; \
    fi; \
    apk del .build-deps

# Application user
RUN addgroup -g 1000 app \
    && adduser -G app -u 1000 -D -s /bin/sh app

# Copy PHP configuration overrides
COPY docker/php/conf.d/ /opt/docker/php/conf.d/
RUN set -eux; \
    cp /opt/docker/php/conf.d/app.ini "$PHP_INI_DIR/conf.d/zz-app.ini"; \
    if [ "${APP_ENV}" = "production" ]; then \
        cp /opt/docker/php/conf.d/prod.ini "$PHP_INI_DIR/conf.d/zz-env.ini"; \
    else \
        cp /opt/docker/php/conf.d/dev.ini "$PHP_INI_DIR/conf.d/zz-env.ini"; \
    fi; \
    if [ "${ENABLE_XDEBUG}" = "true" ]; then \
        cp /opt/docker/php/conf.d/xdebug.ini "$PHP_INI_DIR/conf.d/zz-xdebug.ini"; \
    fi

# Copy application files
COPY --from=builder --chown=app:app /app/vendor ./vendor
COPY --chown=app:app src ./src
COPY --chown=app:app db ./db
COPY --chown=app:app scripts ./scripts
COPY --chown=app:app bootstrap.php phinx.php migrate.sh ./
COPY --chown=app:app composer.json composer.lock ./

RUN chmod +x migrate.sh scripts/wait-for-db.sh

USER app

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD pgrep php-fpm || exit 1

CMD ["php-fpm"]
