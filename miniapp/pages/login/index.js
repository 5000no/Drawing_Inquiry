const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    username: '',
    password: '',
    email: '',
    activationCode: ''
  },

  onInputUsername(e) { this.setData({ username: e.detail.value }) },
  onInputPassword(e) { this.setData({ password: e.detail.value }) },
  onInputEmail(e) { this.setData({ email: e.detail.value }) },
  onInputActivation(e) { this.setData({ activationCode: e.detail.value }) },

  async onLogin() {
    const { username, password } = this.data
    if (!username || !password) {
      return wx.showToast({ title: '请输入用户名和密码', icon: 'none' })
    }
    wx.showLoading({ title: '登录中...' })
    try {
      const res = await api.login(username, password)
      if (res.success) {
        app.globalData.token = res.token
        app.globalData.user = res.user
        wx.setStorageSync('token', res.token)
        wx.setStorageSync('user', res.user)
        wx.showToast({ title: '登录成功', icon: 'success' })
        wx.navigateTo({ url: '/pages/upload/index' })
      } else {
        wx.showToast({ title: res.message || '登录失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: '网络错误', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  async onRegister() {
    const { username, password, email, activationCode } = this.data
    if (!username || !password || !activationCode) {
      return wx.showToast({ title: '用户名、密码、激活码必填', icon: 'none' })
    }
    wx.showLoading({ title: '注册中...' })
    try {
      const res = await api.register({ username, password, email, activation_code: activationCode })
      if (res.success) {
        app.globalData.token = res.token
        app.globalData.user = res.user
        wx.setStorageSync('token', res.token)
        wx.setStorageSync('user', res.user)
        wx.showToast({ title: '注册成功', icon: 'success' })
        wx.navigateTo({ url: '/pages/upload/index' })
      } else {
        wx.showToast({ title: res.message || '注册失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: '网络错误', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  }
})