# PostgreSQL Development Image
FROM postgres:16-alpine

# Copy maintenance scripts and make them available as commands
COPY maintenance /usr/local/bin/maintenance
RUN chmod +x /usr/local/bin/maintenance/* && \
    chmod +x /usr/local/bin/maintenance/_sourced/* && \
    mv /usr/local/bin/maintenance/* /usr/local/bin/ && \
    rmdir /usr/local/bin/maintenance

# Set healthcheck
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD pg_isready -U ${POSTGRES_USER:-postgres} || exit 1
