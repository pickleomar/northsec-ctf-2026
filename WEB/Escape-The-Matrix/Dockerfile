# =========================
# Stage 1 — Build Frontend
# =========================
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# =========================
# Stage 2 — Build Backend (Java 8)
# =========================
FROM maven:3.8.6-openjdk-8 AS backend-build
WORKDIR /build/server

# Copy pom.xml first for better cache usage
COPY server/pom.xml ./pom.xml

# Copy backend source
COPY server/src ./src

# Copy GIF assets into resources (private, packaged in JAR)
COPY server/assets ./src/main/resources/assets

# Copy frontend build artifacts into Spring static resources
COPY --from=frontend-build /app/frontend/dist ./src/main/resources/static

# Build the jar (this will resolve deps + plugins automatically)
RUN mvn -B -q clean package -DskipTests

# =========================
# Stage 3 — Runtime (Java 8)
# =========================
FROM amazoncorretto:8

RUN yum install -y shadow-utils && yum clean all

RUN groupadd -r run-as-group && useradd -r -g run-as-group player

WORKDIR /app

COPY flag.txt /app/flag.txt
RUN chown root:run-as-group /app/flag.txt && chmod 440 /app/flag.txt

COPY --from=backend-build /build/server/target/*.jar app.jar

ENV JAVA_OPTS="\
-Dlog4j2.formatMsgNoLookups=false \
-Dlog4j2.enableJndi=true \
-Dcom.sun.jndi.ldap.object.trustURLCodebase=true \
-Dcom.sun.jndi.rmi.object.trustURLCodebase=true \
"

RUN chown -R player:run-as-group /app

USER player

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
