# 微信小程序 · 图纸上传

本小程序用于：注册/登录用户，并通过移动端上传 PDF 图纸到对应的租户数据库（按激活码隔离）。

## 功能
- 登录、注册（注册需激活码）
- 选择 PDF 文件并上传（`wx.uploadFile`）
- 上传完成后支持下载预览（`wx.downloadFile` + `wx.openDocument`）

## 对接参数
- 登录：`POST /api/mobile/login`，JSON `{ username, password }`
- 注册：`POST /api/mobile/register`，JSON `{ username, password, email?, activation_code }`
- 上传：`POST /api/mobile/upload`
  - Header：`Authorization: Bearer <token>`（可选）
  - FormData：`product_code`、`token`（任选其一或同时）
  - File：`name: file`（或 `pdf_file`）
- 预览：后端返回 `pdf_url`，直接用于下载/打开，已携带 `token`

## 域名与 HTTPS
为在真机使用，请完成以下配置：
1. 服务端必须是 `HTTPS` 域名且证书有效（例如使用自有域名 + Cloudflare/Let’s Encrypt）。
2. 在微信公众平台 → 开发 → 开发管理 → 开发设置：
   - 配置 `request合法域名` 与 `uploadFile合法域名`（填写你的服务域名）。
3. 开发阶段可在微信开发者工具的“详情”中临时关闭“`不校验合法域名`”，或使用局域网地址进行联调（但真机上仍需 HTTPS 域名）。

## 环境变量与修改
- 默认后端地址写在 `miniapp/app.js` 的 `globalData.baseURL`：
  - 局域网示例：`http://192.168.14.122:5000`
  - 外网示例（Cloudflare 隧道域名）：`https://intelligence-mesa-comparisons-detective.trycloudflare.com`
  - 正式环境请替换为你自己的 HTTPS 域名

## 导入与运行
1. 打开微信开发者工具，选择“导入项目”，目录选择 `miniapp/`。
2. 如果没有 AppID，可临时使用 `touristAppId`（仅开发调试）。
3. 修改 `app.js` 的 `baseURL` 指向你的服务地址。
4. 运行后：
   - 先在“登录/注册”页完成登录或注册
   - 进入“上传”页，填写产品号、选择 PDF 并上传
   - 上传成功后可预览或复制链接

## 注意事项
- 产品号在同租户库内需唯一，重复会返回错误提示。
- 后端会按激活码分目录存储 PDF，并记录到对应租户数据库。
- 若报“未授权或令牌无效”，请确保登录成功并在上传时携带 `token`。
- 若报网络错误，请检查：域名白名单、HTTPS证书、外网/内网连通性。