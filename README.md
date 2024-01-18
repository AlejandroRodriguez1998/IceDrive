# IceDrive Blob Service ~~Template~~

~~This repository contains the project template for the Blob service proposed as laboratory work for the students
of Distributed Systems in the course 2023-2024.~~

Este repositorio contiene la plantilla del proyecto del servicio Blob propuesto como trabajo de laboratorio para los alumnos
de Sistemas Distribuidos en el curso 2023-2024.

Soy **Alejandro Paniagua Rodriguez** y tengo asignado el servicio de **blob**. 🗁

##  🗄 Tabla de Contenido

- [Requisitos](#%EF%B8%8F-requisitos)
- [Ejecución](#%EF%B8%8F-ejecución)
- [Testing](#-testing)
- [Documentación](#-documentación)
- [Archivos](#-archivos)
- [Contacto](#-contacto)

## ⚙️ Requisitos

- Python 3.8
- Ice 3.7
- IceStorm

## 🛠️ Ejecución

- 1 PASO: Debemos instalar el servicio:

  `pip install .`
 
  - En caso de error seria el siguiente:

      `pip3 install .`
    
 - 2 PASO: Iniciar el servicio con el comando:

    `icedrive-blob --Ice.Config=config/blob.config`
 
 Si todo ha salido correctamente al ejecutar, saldria un mensaje parecido a lo siguiente:
 
 ```
 INFO:root:Proxy: 144A4B97-F75E-4496-9080-BF3E338CAEDA -t -e 1.1:tcp -h 192.168.0.89 -p 55119 -t 60000

 INFO:root:Received Blob Service: E15A0A29-6BBF-4EE8-A217-22F09507D859 -t -e 1.1:tcp -h 192.168.0.218 -p 40141 -t 60000
 INFO:root:Received Directory Service: BE2E70D8-E8B3-491C-9B2F-69D17162D84F -t -e 1.1:tcp -h 192.168.0.218 -p 44041 -t 60000
 INFO:root:Received Authentication Service: 74097BC1-1B4B-4961-8083-402CB129D844 -t -e 1.1:tcp -h 192.168.0.218 -p 35881 -t 60000
 ```

## ✔ Testing

Para ejecutar el testing solo tenemos que ubicarnos en la carpeta **_tests_** donde pondremos el siguiente comando:

`python test.py --Ice.Config=../config/blob.config`

**En caso de error** tenemos que darle permisos al archivo con el siguiente comando: `sudo chmod +x test.py`

Al ejecutar el testing nos saldra un mensaje con la siguiente informanción:

```
Para estos test se crean:
· Un servicio de autenticación:
 8A00768F-7C0C-4CFE-880A-7A60879431D8 -t -e 1.1:tcp -h localhost -p 10004 -t 60000

· Un servicio de descubrimiento:
 74EAE096-AEA9-4A3A-9373-E9D51477B1D8 -t -e 1.1:tcp -h 192.168.0.89 -p 55719 -t 60000

· Donde se anuncia el autenticador:
Received Authentication Service: 8A00768F-7C0C-4CFE-880A-7A60879431D8 -t -e 1.1:tcp -h localhost -p 10004 -t 60000

· Un blob service:
D237E252-17FF-49CE-9396-4956C4C0B1D8 -t -e 1.1:tcp -h 192.168.0.89 -p 55719 -t 60000

· Otro blob service:
A93057D9-E6D5-4136-81A4-73026474B1D8 -t -e 1.1:tcp -h localhost -p 10003 -t 60000

· Un blob query:
345BDE5E-A494-42E4-BD78-D85C2B8631D8 -t -e 1.1:tcp -h 192.168.0.89 -p 55719 -t 60000

·TEST 1: Verificar usuario que existe --> test_user
User user_existente verified

·TEST 2: Verificar usuario que no existe --> test_user2
User user_no_existente not verified

·TEST 3: Simular la subida de un blob con el usuario (user_existente)
No response received in 5 seconds
Blob id not exists with BlobQuery
Blob uploaded with ID: 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe

·TEST 4: Simular la subida de un blob con el usuario (user_no_existente)
Blob not uploaded with ID:

·TEST 5: Simular la descarga de un blob con el usuario (user_existente)
DataTransferPrx: 81A59494-F47E-49B0-ADE9-96E4A1AC31D8 -t -e 1.1:tcp -h 192.168.0.89 -p 55719 -t 60000

·TEST 6: Simular la descarga de un blob con el usuario (user_no_existente)
DataTransferPrx: None

·TEST 7: Simular la subida de un blob que ya existe en otro servicio
Blob id exists with BlobQuery
Blob not uploaded with ID: 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe

·TEST 8: Descargar un blob por diferido
Blob downloaded with BlobQuery
DataTransferPrx: E2B26645-F251-4DDD-9BDA-616032EEB1D8 -t -e 1.1:tcp -h 192.168.0.89 -p 55719 -t 60000

·TEST 9: Link de un blob por diferido
Antes de la llamada el blob tiene: 1
Blob linked with BlobQuery
Después de la llamada el blob tiene: 2

·TEST 10: Unlink de un blob por diferido
Antes de la llamada el blob tiene: 2
Blob unlinked with BlobQuery
Blob unliked con exito: 1
```

## 📚 Documentación

El servicio de almacenamiento utiliza sumas hash (como SHA256) para asignar identificadores únicos a los blobs (contenidos de archivos) en un sistema de archivos remoto. Al subir un archivo, el servicio verifica si el blob ya existe mediante su hash, ahorrando espacio si es duplicado. Además, se registra el número de enlaces a un blob, eliminándolo automáticamente cuando ya no está enlazado. El servicio persistente tiene dos interfaces, ::IceDrive::DataTransfer para la gestión de transferencias y ::IceDrive::BlobService para la implementación del servicio, permitiendo la configuración del directorio de persistencia.

- Toda la documentacion se encuentra en el [enlace al documento del laboratorio.](https://campusvirtual.uclm.es/pluginfile.php/446956/mod_resource/content/7/Lab%20P1-rev2.pdf)

### DataTransfer

- `read()`: El destinatario de la transferencia solicita el siguiente bloque de bytes, retorna un bloque de bytes del tamaño solicitado.
  
- `close()`: Destinatario de la transferencia ya no desea seguir con la transferencia, debe eliminar la instancia de ::IceDrive::DataTransfer.

### BlobService

- `link()`: Incrementa el número de veces que un blob se encuentra enlazado.

- `unlink()`: Decrementa el número de veces que un blob se encuentra enlazado, cuando el blob no se encuentre enlazado, se eliminará.

- `upload()`: Subir un nuevo blob, cuando finalice la transferencia, devolverá el blobId.

   - Ahora upload tiene que validar un usuario.

- `download()`: Devolverá una instancia de ::IceDrive::DataTransfer para permitir la descarga del mismo.

   - Ahora download tiene que validar un usuario.

### Discovery y diferido
- Todos los servicios deben publicar y suscribirse a anuncios, enviar invocaciones periódicas y gestionar cooperaciones y errores en la selección de microservicios.

- Cuando un servicio no puede atender una solicitud, intentará resolverla colaborando con servicios similares, utilizando un mecanismo de almacenamiento y respuesta temporizado, reenviando la solución al cliente.

La nueva documentacion se encuentra en el [enlace al segundo documento del laboratorio.](https://campusvirtual.uclm.es/pluginfile.php/480550/mod_resource/content/10/Lab%20P2.rev3.pdf)

- **Class Discovery:**

   - `announceAuthentication()` : Almacena el servicio Authentication.
   
   - `announceDirectoryService()`: Almacena el servicio Directory.

   - `announceBlobService()`: Almacena el servicio Blob evitandose a si mismo

- **Class BlobQuery:**

   - `downloadBlob()`: Manda una peticion a dowload() del servicio Blob.

   - `blobIdExists()`: Manda una peticion a upload() del servicio Blob.

   - `linkBlob()`: Manda una peticion a link() del servicio Blob.

   - `unlinkBlob()`: Manda una peticion unlink() del servicio Blob.

- **Class BlobQueryResponse:**

   - `downloadBlob()`: Ha recibio una respuesta de downloadBlob().

   - `blobExists()`: Ha recibio una respuesta de blobIdExists().

   - `blobLinked()`: Ha recibio una respuesta de linkBlob().

   - `blobUnlinked()`: Ha recibio una respuesta de unlinkBlob().

## 📝 Archivos

Tenemos la siguiente estructura:

```
├── config
│   │ 
│   ├── blob.config -->  Donde estan las configuraciones para app.py y test.py
│   │   
│   ├── icebox.config --> Configuracion para el comando icebox en run_icestorm
│   │   
│   └── icestorm.config --> Configuración para el resto de IceStorm
│   
├── icedrive_blob
│   │
│   ├── app.py --> Fichero python que arranca el servicio y lo pone en marcha
│   │ 
│   ├── blob.py --> Fichero python donde tiene toda la logica de ejecucion/metodos del servicio
│   │  
│   ├── delayed_response.py --> Fichero python donde esta la logica para el manejo de diferido.
│   │  
│   ├── discovery.py --> Fichero python donde tiene la logica para el anunciamiento
│   │ 
│   └── icedrive.ice --> La interfaz ice donde tenemos los metodos que implementar en blob.py
│ 
├── test
│   │ 
│   └── test.py --> Fichero python que ejecuta las pruebas del apartado testing
│ 
├── pyproject.toml --> Archivo de configuración para lanzar el servicio mas comodamente
│ 
├── README.md --> Fichero donde estas leyendo todo esto
│ 
└── run_icestorm --> ejecutable para poder lanzar e instalar IceStorm y sus topics

```

## ☎ Contacto

Cualquier duda o consulta, escribidme a mi correo: alejandro.paniagua1@alu.uclm.es.
