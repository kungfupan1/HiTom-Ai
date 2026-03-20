<template>
  <div class="content-manage">
    <el-row :gutter="20">
      <!-- 左侧：分类列表 -->
      <el-col :span="6">
        <el-card class="category-card">
          <template #header>
            <div class="card-header">
              <span>内容分类</span>
              <el-button type="primary" size="small" @click="showCategoryDialog()">新增</el-button>
            </div>
          </template>
          <el-menu :default-active="activeCategory" @select="selectCategory">
            <el-menu-item v-for="cat in categories" :key="cat.id" :index="String(cat.id)">
              <span>{{ cat.icon || '📁' }} {{ cat.category_name }}</span>
              <el-button link type="primary" size="small" @click.stop="showCategoryDialog(cat)">编辑</el-button>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 中间：栏目列表 -->
      <el-col :span="6">
        <el-card class="item-card" v-if="activeCategory">
          <template #header>
            <div class="card-header">
              <span>栏目列表</span>
              <el-button type="primary" size="small" @click="showItemDialog()">新增</el-button>
            </div>
          </template>
          <el-menu :default-active="activeItem" @select="selectItem">
            <el-menu-item v-for="item in currentItems" :key="item.id" :index="String(item.id)">
              <span>{{ item.icon || '📄' }} {{ item.item_name }}</span>
              <el-button link type="primary" size="small" @click.stop="showItemDialog(item)">编辑</el-button>
            </el-menu-item>
          </el-menu>
        </el-card>
        <el-empty v-else description="请先选择分类" />
      </el-col>

      <!-- 右侧：卡片列表 -->
      <el-col :span="12">
        <el-card class="cards-card" v-if="activeItem">
          <template #header>
            <div class="card-header">
              <span>内容卡片</span>
              <el-button type="primary" size="small" @click="showCardDialog()">新增</el-button>
            </div>
          </template>
          <el-table :data="currentCards" stripe>
            <el-table-column prop="icon" label="图标" width="60" />
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="description" label="简介" show-overflow-tooltip />
            <el-table-column prop="contact_info" label="联系方式" width="120" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="showCardDialog(row)">编辑</el-button>
                <el-button link type="danger" @click="deleteCard(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        <el-empty v-else description="请先选择栏目" />
      </el-col>
    </el-row>

    <!-- 分类对话框 -->
    <el-dialog v-model="categoryDialogVisible" :title="categoryForm.id ? '编辑分类' : '新增分类'" width="400px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="分类Key">
          <el-input v-model="categoryForm.category_key" placeholder="如：shrimp, service" />
        </el-form-item>
        <el-form-item label="分类名称">
          <el-input v-model="categoryForm.category_name" placeholder="如：云端养虾" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="categoryForm.icon" placeholder="emoji 或图标名" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>

    <!-- 栏目对话框 -->
    <el-dialog v-model="itemDialogVisible" :title="itemForm.id ? '编辑栏目' : '新增栏目'" width="500px">
      <el-form :model="itemForm" label-width="80px">
        <el-form-item label="栏目Key">
          <el-input v-model="itemForm.item_key" placeholder="如：openclaw, skills" />
        </el-form-item>
        <el-form-item label="栏目名称">
          <el-input v-model="itemForm.item_name" placeholder="如：OpenClaw部署" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="itemForm.icon" placeholder="emoji 或图标名" />
        </el-form-item>
        <el-form-item label="路由路径">
          <el-input v-model="itemForm.route_path" placeholder="如：/shrimp/openclaw" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="itemForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>

    <!-- 卡片对话框 -->
    <el-dialog v-model="cardDialogVisible" :title="cardForm.id ? '编辑卡片' : '新增卡片'" width="600px">
      <el-form :model="cardForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="cardForm.title" placeholder="如：OpenClaw" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="cardForm.icon" placeholder="emoji" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="cardForm.description" type="textarea" :rows="3" placeholder="产品简介" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="cardForm.contact_info" placeholder="如：微信号 waterborn911" />
        </el-form-item>
        <el-form-item label="扩展数据">
          <el-input v-model="extraDataJson" type="textarea" :rows="3" placeholder='JSON 格式，如：{"price": "¥99", "tag": "热门"}' />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="cardForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="cardForm.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cardDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCard">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const categories = ref([])
const activeCategory = ref(null)
const activeItem = ref(null)

const categoryDialogVisible = ref(false)
const itemDialogVisible = ref(false)
const cardDialogVisible = ref(false)

const categoryForm = ref({ category_key: '', category_name: '', icon: '', sort_order: 0 })
const itemForm = ref({ item_key: '', item_name: '', icon: '', route_path: '', sort_order: 0 })
const cardForm = ref({ title: '', icon: '', description: '', contact_info: '', extra_data: null, sort_order: 0, is_enabled: true })
const extraDataJson = ref('')

const currentItems = computed(() => {
  const cat = categories.value.find(c => c.id === Number(activeCategory.value))
  return cat?.items || []
})

const currentCards = computed(() => {
  const item = currentItems.value.find(i => i.id === Number(activeItem.value))
  return item?.cards || []
})

const loadCategories = async () => {
  try {
    const res = await request.get('/admin/content/categories')
    categories.value = res
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

const selectCategory = (id) => {
  activeCategory.value = id
  activeItem.value = null
}

const selectItem = (id) => {
  activeItem.value = id
}

// 分类操作
const showCategoryDialog = (cat = null) => {
  if (cat) {
    categoryForm.value = { ...cat }
  } else {
    categoryForm.value = { category_key: '', category_name: '', icon: '', sort_order: 0 }
  }
  categoryDialogVisible.value = true
}

const saveCategory = async () => {
  try {
    if (categoryForm.value.id) {
      await request.put(`/admin/content/categories/${categoryForm.value.id}`, categoryForm.value)
    } else {
      await request.post('/admin/content/categories', categoryForm.value)
    }
    ElMessage.success('保存成功')
    categoryDialogVisible.value = false
    loadCategories()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

// 栏目操作
const showItemDialog = (item = null) => {
  if (item) {
    itemForm.value = { ...item }
  } else {
    itemForm.value = { item_key: '', item_name: '', icon: '', route_path: '', sort_order: 0 }
  }
  itemDialogVisible.value = true
}

const saveItem = async () => {
  try {
    if (itemForm.value.id) {
      await request.put(`/admin/content/items/${itemForm.value.id}`, itemForm.value)
    } else {
      await request.post(`/admin/content/categories/${activeCategory.value}/items`, itemForm.value)
    }
    ElMessage.success('保存成功')
    itemDialogVisible.value = false
    loadCategories()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

// 卡片操作
const showCardDialog = (card = null) => {
  if (card) {
    cardForm.value = { ...card }
    extraDataJson.value = card.extra_data ? JSON.stringify(card.extra_data, null, 2) : ''
  } else {
    cardForm.value = { title: '', icon: '', description: '', contact_info: '', extra_data: null, sort_order: 0, is_enabled: true }
    extraDataJson.value = ''
  }
  cardDialogVisible.value = true
}

const saveCard = async () => {
  try {
    // 解析 JSON
    if (extraDataJson.value.trim()) {
      try {
        cardForm.value.extra_data = JSON.parse(extraDataJson.value)
      } catch {
        ElMessage.warning('扩展数据 JSON 格式错误')
        return
      }
    }

    if (cardForm.value.id) {
      await request.put(`/admin/content/cards/${cardForm.value.id}`, cardForm.value)
    } else {
      await request.post(`/admin/content/items/${activeItem.value}/cards`, cardForm.value)
    }
    ElMessage.success('保存成功')
    cardDialogVisible.value = false
    loadCategories()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const deleteCard = async (card) => {
  try {
    await ElMessageBox.confirm('确定删除该卡片？', '提示', { type: 'warning' })
    await request.delete(`/admin/content/cards/${card.id}`)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.content-manage {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-card, .item-card, .cards-card {
  min-height: 500px;
}

.el-menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>