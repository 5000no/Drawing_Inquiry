const app = getApp()

const getBaseURL = () => {
  return app?.globalData?.baseURL || 'http://localhost:5000'
}

// 通用请求封装
const request = (path, method = 'GET', data = {}) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getBaseURL()}${path}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json'
      },
      success: res => {
        resolve(res.data)
      },
      fail: err => reject(err)
    })
  })
}

// 登录
const login = (username, password) => {
  return request('/api/mobile/login', 'POST', { username, password })
}

// 注册（带激活码）
const register = (payload) => {
  return request('/api/mobile/register', 'POST', payload)
}

// 上传PDF
const uploadPDF = ({ token, productCode, filePath }) => {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${getBaseURL()}/api/mobile/upload`,
      filePath,
      name: 'file', // 后端支持 file 或 pdf_file，这里统一使用 file
      formData: {
        product_code: productCode,
        token // 也可以通过 Authorization 传递，这里两者都支持
      },
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: res => {
        try {
          const data = JSON.parse(res.data)
          resolve(data)
        } catch (e) {
          resolve({ success: false, message: '解析上传响应失败' })
        }
      },
      fail: err => reject(err)
    })
  })
}

module.exports = {
  getBaseURL,
  login,
  register,
  uploadPDF
}