# 七牛自定义数据处理程序示例


**注意,这个是旧版处理程序,已经废弃,针对新版处理程序,可参见本人编写的https://github.com/Xavier-Lam/qiniu-ufop**

当七牛既有的数据处理功能不能满足用户对文件资源的操作时，用户可以添加自定义数据处理资源。七牛可以免费开启一个512M内存的单核实例运行，部署方式类似生成docker镜像，将镜像部署至七牛服务端，并提供一个run命令运行你的程序。这边以一个计算文件指定范围摘要的小脚本来简单描述一下如何构建一个七牛自定义数据处理程序。

文档地址 http://developer.qiniu.com/article/index.html#dora-ufop

## 注册自定义处理程序

根据文档，在七牛控制台上创建一个自定义数据处理程序。

## 编写处理程序

处理程序可以用任何(直接或编译后)能在ubuntu 14.04 上运行的语言编写。该脚本需监听**9100**端口，当用户发起访问请求时，七牛会向 **/uop** 发起一个post请求，请求格式如下

    POST /uop HTTP/1.1
    Content-Type: application/json

    {
        "cmd": "<ufop>/<param>",
        "src": {
            "url": "http://<host>:<port>/<path>",
            "mimetype": "<mimetype>",
            "fsize": <filesize>,
            "bucket": <bucket>,
            "key": <key>
        }
    }

参数解释如下

    /uop：固定的请求规格，您的服务程序可以选择识别或者忽略。
    cmd：固定的 QueryString，外部访问时使用的自定义数据处理指令（包括参数）会被原样的传入。
    <ufop>：cmd 指令的一部分，通常为自定义数据处理名称。
    <param>：如果您的服务程序需要外部通过参数调整处理方式，那么可以将参数信息放在这里。
    <url>：通过该 url 可以获取到待处理的数据，其可能是被访问的资源本身，也可能是前一个数据处理或自定义数据处理处理后的输出内容（使用管道）。
    <mimetype>：待处理文件的数据类型。
    <fsize>：待处理文件的文件大小，以字节为单位。
    <bucket>：资源所在的bucket的唯一标识ID（不是bucket name
    <key>：资源的key文件名，会剥离文件路径，如 key 为 a/b/c.txt 结果就是 c.txt

你需要编写一个监听9100 端口，在/uop 路径下接收以上POST请求，并返回一个HTTP响应的程序。HTTP响应可以是任何格式，既可以是处理完成的文件流，也可以是处理结果数据。

程序的日志直接打在控制台就可以在实例日志中查看到你的日志了。

## 编写构建脚本

构建脚本是一个yaml脚本，命名必须为**ufop.yaml**，并放置在根目录下。示例格式如下：

    image: <base_image>
    build_script:
    - <command1>
    - <command2>
    - <command3>
    - ...
    run: <run_command>

参数解释如下

    image：创建镜像时的基础镜像，ubuntu 或者以前创建好的一个镜像加版本，如：test.v7
    build_script：创建镜像时的脚本，在这里进行安装环境等操作
    run：运行程序的启动命令，对应的服务需要监听 9100 端口
    $RESOURCE：资源存放的临时目录，在镜像构建时，用户上传的 tar 包会被自动解压到这个目录下，然后根据 yaml 中的运行脚本，把资源拷贝到当前目录或其它需要的目录下，构建结束后这个目录会被删除。如果用户需要将其上传的资源放在当前目录下，需要在 ufop.yml 的 build_script 中加入指令：sudo mv $RESOURCE/* .
    $PWD：当前目录也是以后的的工作目录

这个文件类似dockerfile，只不过把他表述成了yaml格式。在编写构建脚本时，有三个需要注意的点。第一点是在开头要有一句sudo apt-get update 更新apt-get源，否则你啥也下不到；第二点是在apt-get安装时需要有-y参数，否则会有异常；第三点是脚本的结束要包含**mv $RESOURCE/* .**，将上传的需要执行的代码拷贝至工作目录。在编译期，你拥有sudo权限，在运行时，你只拥有普通用户权限。

## 上传你的镜像

目录的组织结构应如下所示

    .
    ├── ufop.yaml
    ├── your file
    └── your file

两种方式，一种是手动打包你的应用，将这个文件夹打包成.tar格式，在七牛web控制台点击上传构建来上传；另一种是使用七牛的控制台工具，下载地址：http://developer.qiniu.com/article/dora/ufop/ufop-cli.html 首先运行

    $ qufopctl login -u <username> -p <password>
    或
    $ qufopctl login -u <access key> -p <secret key>
    或
    $ qufopctl login 进入命令行交互界面进行登录

登陆。登陆后会自行退出，不用担心。登陆后输入

	qufopctl build <app> [-f <folder>] [-d <description>]

| 名称 | 说明 |
| --- | --- |
| app | 你的自定义数据处理名称 |
| folder | 设置本地包含二进制程序和 ufop.yaml 的文件夹路径,不填为当前路径 |
| description | 对当前版本的描述 |

就上传并开始编译你的镜像了。你的镜像可以在版本列表中看到，编译日志也可查看，编译失败的话，可以根据编译日志查看哪里失败了。编译需要较常时间，稍安勿躁。

## 启动实例并使用

在实例列表中可以启动你的实例，成功启动后，你的小程序就在运行了。注意，编译成功不代表你的程序就能够成功运行，因为你的run语句可能有误，也可能你的程序中有bug，使程序中断运行了。

使用的方式是 

	<yourfileurl>?<yourappname>/<params>

如

    http://7xivot.com1.z0.glb.clouddn.com/fonts/full/方正准圆_GBK?qhash/md5

也可上传后自动异步触发或对已有资源异步触发。其他使用方式可参见七牛文档

	http://developer.qiniu.com/article/developer/persistent-fop.html



## 我的示例

本文件夹下包含一个示例程序。可计算文件前多少字节的摘要。byte数可选，默认256kb，最大4M；算法可选，默认MD5，可选SHA1、SHA256。

	计算前1024字节的md5摘要
	http://7xivot.com1.z0.glb.clouddn.com/fonts/full/方正准圆_GBK?xvl-256kb-md5/1024
    计算前256kb的sha256摘要
    http://7xivot.com1.z0.glb.clouddn.com/fonts/full/方正准圆_GBK?xvl-256kb-md5/sha256
    计算前1024字节的sha1摘要
    http://7xivot.com1.z0.glb.clouddn.com/fonts/full/方正准圆_GBK?xvl-256kb-md5/sha1/1024

我的响应

	{"mimetype": "image/png", "digestsize": 1024, "digest": "37d4072f92cd8df4d9cb29c2e3bc9eaf", "fsize": 10086, "algorithm": "openssl_md5"}
