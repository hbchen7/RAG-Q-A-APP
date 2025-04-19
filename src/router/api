import request from '@/utils/request'

/**
 * @description 创建一个新的助手
 * @param {object} data - 创建助手所需的数据
 * @param {string} [data.title='新助手'] - 助手标题，默认为 '新助手'
 * @param {string} [data.username='root'] - 用户名，默认为 'root'
 * @param {string} data.prompt - 助手提示词
 * @param {string} [data.knowledge_Id] - 知识库 ID (可选)
 * @returns {Promise} 返回一个 Promise 对象，包含创建的助手信息
 */
export const createAssistantAPI = (data) => {
  return request.post('/assistant/create', data)
}

/**
 * @description 获取指定用户的助手列表
 * @param {object} params - 查询参数
 * @param {string} params.username - 需要查询助手列表的用户名
 * @returns {Promise} 返回一个 Promise 对象，包含用户的助手列表 (按创建时间升序排序)
 */
export const getAssistantListAPI = (params) => {
  return request.get('/assistant/list', { params })
}

/**
 * @description 更新指定助手的信息
 * @param {string} assistantId - 要更新的助手的 ID
 * @param {object} data - 更新助手所需的数据
 * @param {string} data.title - 新的助手标题
 * @param {string} data.prompt - 新的助手提示词
 * @param {string} [data.knowledge_Id] - 新的知识库 ID (可选)
 * @returns {Promise} 返回一个 Promise 对象，包含更新后的助手信息
 */
export const updateAssistantAPI = (assistantId, data) => {
  // 注意：username 在请求体中会被后端忽略，无需传递或后端会自动处理
  return request.put(`/assistant/update/${assistantId}`, data)
}

/**
 * @description 删除指定的助手及其关联的所有会话和聊天记录
 * @param {object} params - 查询参数
 * @param {string} params.assistant_id - 要删除的助手的 ID
 * @returns {Promise} 返回一个 Promise 对象，包含删除操作的结果信息 (例如：{ message: "..." })
 */
export const deleteAssistantAPI = (params) => {
  // 根据后端 assistantRouter.py 定义，assistant_id 是查询参数
  return request.delete('/assistant/delete', { params })
}
