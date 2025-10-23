const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    productCode: '',
    tempFilePath: '',
    uploadedId: null,
    uploadedFile: '',
    pdfUrl: ''
  },

  onShow() {
    if (!app.globalData.token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      wx.navigateTo({ url: '/pages/login/index' })
    }
  },

  onInputCode(e) { this.setData({ productCode: e.detail.value }) },

  onChooseFile() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['pdf'],
      success: (res) => {
        const file = res.tempFiles?.[0]
        if (!file) return
        this.setData({ tempFilePath: file.path })
        wx.showToast({ title: '已选择PDF', icon: 'success' })
      },
      fail: () => wx.showToast({ title: '选择文件失败', icon: 'none' })
    })
  },

  async onUpload() {
    const { productCode, tempFilePath } = this.data
    if (!productCode || !tempFilePath) {
      return wx.showToast({ title: '请填写产品号并选择PDF', icon: 'none' })
    }
    wx.showLoading({ title: '上传中...' })
    try {
      const res = await api.uploadPDF({
        token: app.globalData.token,
        productCode,
        filePath: tempFilePath
      })
      if (res.success) {
        const { id, product_code, pdf_path, pdf_url } = res.data
        this.setData({ uploadedId: id, uploadedFile: pdf_path, pdfUrl: pdf_url })
        wx.showToast({ title: '上传成功', icon: 'success' })
      } else {
        wx.showToast({ title: res.message || '上传失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: '网络错误', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  onPreview() {
    const { pdfUrl } = this.data
    if (!pdfUrl) return
    // 下载到本地并使用 openDocument 预览
    wx.downloadFile({
      url: pdfUrl,
      success: (res) => {
        const filePath = res.tempFilePath
        wx.openDocument({
          filePath,
          showMenu: true,
          fileType: 'pdf',
          success: () => wx.showToast({ title: '打开成功', icon: 'success' }),
          fail: () => wx.showToast({ title: '打开失败', icon: 'none' })
        })
      },
      fail: () => wx.showToast({ title: '下载失败', icon: 'none' })
    })
  },

  onCopyLink() {
    const { pdfUrl } = this.data
    if (!pdfUrl) return
    wx.setClipboardData({
      data: pdfUrl,
      success: () => wx.showToast({ title: '链接已复制', icon: 'success' })
    })
  }
})