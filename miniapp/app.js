// 简易全局配置
App({
  globalData: {
    // 默认使用内网或外网域名（二选一按需修改）
    // baseURL: 'http://192.168.14.122:5000',
    baseURL: 'https://cancer-sat-henderson-mtv.trycloudflare.com',
    token: '',
    user: null
  },
  onLaunch() {
    const token = wx.getStorageSync('token') || ''
    const user = wx.getStorageSync('user') || null
    if (token) this.globalData.token = token
    if (user) this.globalData.user = user
  }
})