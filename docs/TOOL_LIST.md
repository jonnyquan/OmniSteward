# 工具

**注意，本文档正在更新中，请以代码为准**

## 可用工具

### 内建工具

这些工具是OmniSteward的内建工具，不需要额外安装（但可能需要配置），直接使用即可。

- `discover_program`: 查找电脑程序，支持模糊匹配
- `launch_program`: 启动程序
- `bemfa_control`: 巴法云平台设备控制，配置详见[bemfa_control](./TOOL_LIST.md#bemfa_control)
- `web_search`: 百度搜索信息查询
- `ask_kimi`: 通过Kimi AI助手查询信息, 首次使用需要在弹出的浏览器登录Kimi，然后关闭浏览器
- `step_web_search`: [使用stepfun的web搜索工具](https://platform.stepfun.com/docs/guide/web_search)，支持自然语言检索, 仅在使用step系列模型时可用
- `browser`: 打开网页
- `cmd`: 执行命令行命令
- `write_file`: 写入文件
- `read_file`: 读取文件
- `zip_dir`: 压缩文件夹
- `prepare_download`: 准备下载文件, 返回文件下载链接
- `list_dir`: 列出文件夹内容
- `enhanced_everything`: 增强版everything工具，支持使用自然语言检索

### 拓展工具
这些工具需要另外安装
- `omni_ha.HomeAssistant`: 通过自然语言控制HomeAssistant智能家居设备, 请安装配置[omni-ha](https://github.com/OmniSteward/omni-ha)

## 指定使用哪些工具

在`config.py`中，`tool_names`列表中指定使用哪些工具。

## 创建自定义工具

参见[steward-utils](https://github.com/OmniSteward/steward-utils)项目


## 部分内建工具概览

### bemfa_control

描述: 巴法云平台设备控制
配置项:
- `bemfa_uid`: 巴法云平台UID
- `bemfa_topic`: 巴法云平台Topic

### ask_kimi

描述: 通过Kimi AI助手查询信息, 首次使用需要在弹出的浏览器登录Kimi，然后关闭浏览器
配置项:
- `kimi_profile_path`: Chrome用户数据目录（可选，用于Kimi AI功能，不填则使用默认路径）


