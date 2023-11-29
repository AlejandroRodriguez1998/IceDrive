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

- Python 3
- Ice 3.7

## 🛠️ Ejecución

- 1 PASO: Debemos instalar el servicio:

  `pip install .`
 
  - En caso de error seria el siguiente:

      `pip3 install .`
    
 - 2 PASO: Iniciar el servicio con el comando:

    `icedrive-blob --Ice.Config=config/blob.config`
 
 Si todo ha salido correctamente al ejecutar, saldria un mensaje parecido a lo siguiente:
 
 ```
 INFO:root:Proxy: 5650A7F3-149E-46D6-9259-D93A668392B8 -t -e 1.1:tcp -h 10.0.2.15 -p 41223 -t 60000
 ```

## ✔ Testing

Para ejecutar el testing solo tenemos que ubicarnos en la carpeta **_test_** donde pondremos el siguiente comando:

`python3 test_fileService.py <proxy_BlobService>`

Donde **_<proxy_BlobService>_** es lo que nos proporciona  la ejecución del servicio.

Un ejemplo:

``` 
python3 test_blob.py "B8A85B74-0E7E-4A9A-9639-2A67D46591F6 -t -e 1.1:tcp -h 10.0.2.15 -p 33195 -t 60000"
```

**En caso de error** tenemos que darle permisos al archivo con el siguiente comando: `sudo chmod +x test_blob.py`.

Al ejecutar el testing nos saldra un mensaje con la siguiente informanción:

```
TEST 1: Simular la subida de un blob
Blob uploaded with ID: 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe

TEST 2: Simular la subida de un blob con diferente nombre pero con mismo contenido
Los blobIds son iguales entonces subida no realizada

TEST 3: Simular la subida del blob del test 1
Los blobIds son iguales entonces subida no realizada

TEST 4: Simulacion de descarga del ID --> 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe
Blob downloaded with proxy: 50CDCD3B-3FBD-43DF-B468-42CF4CDD11F6 -t -e 1.1:tcp -h 10.0.2.15 -p 33195 -t 60000

TEST 5: Simulacion de descarga del ID --> 1 (no existe)
Correctamente manejado el intento de descargar un blob inexistente

TEST 6: Simulacion el enlace del ID --> 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe
Blob 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe linked.

TEST 7: Simulacion el enlace del ID --> 1 (no existe)
Correctamente manejado el intento de enlazar un blob inexistente

TEST 8: Simulacion el desenlance del ID --> 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe
Blob 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe unlinked.

TEST 9: Simulacion el desenlance del ID --> 922b553e3ecae8b0ac42cb63d2cbf461078f1f5a2e91e480a2b0b6fac8584dfe
Blob ya no existe por lo tanto exception UnknownBlob.

TEST 10: Simulacion el desenlance del ID --> 1 (no existe)
Correctamente manejado el intento de desenlazar un blob inexistente
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

- `download()`: Devolverá una instancia de ::IceDrive::DataTransfer para permitir la descarga del mismo.

## 📝 Archivos

Tenemos la siguiente estructura:

```
├── config
│   │ 
│   └── blob.config -->  Donde estan las configuraciones para app.py
│   
├── icedrive_blob
│   │
│   ├── app.py --> Fichero python que arranca el servicio y lo pone en marcha
│   │ 
│   ├── blob.py --> Fichero python donde tiene toda la logica de ejecucion/metodos del servicio
│   │  
│   └── icedrive.ice --> La interfaz ice donde tenemos los metodos que implementar en blob.py
│ 
├── test
│   │ 
│   └── test_blob.py --> Fichero python que ejecuta las pruebas del _testing_
│ 
├── pyproject.toml --> Archivo de configuración
│ 
└── README.md --> Fichero donde estas leyendo todo esto

```

## ☎ Contacto

Cualquier duda o consulta, escribid a mi correo: alejandro.paniagua1@alu.uclm.es.
