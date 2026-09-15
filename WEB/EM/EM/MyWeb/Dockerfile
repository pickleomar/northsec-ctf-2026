FROM mcr.microsoft.com/dotnet/sdk:8.0
WORKDIR /app

# Copier les sources
COPY *.csproj ./
RUN dotnet restore

COPY . ./
RUN dotnet publish -c Release -o out

# Flag
RUN echo "NSC{R4z0r_3ng1n3_sst1_byp4ss_m4st3r_2109}" > /flag.txt && \
    chmod 444 /flag.txt

EXPOSE 8080
WORKDIR /app/out
ENTRYPOINT ["dotnet", "dotnet-ssti-ctf.dll"]
