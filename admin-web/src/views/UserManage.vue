<template>
  <div class="user-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户列表</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索用户名"
              style="width: 200px;"
              clearable
              @keyup.enter="loadUsers"
            >
              <template #append>
                <el-button @click="loadUsers">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </div>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="points" label="积分" width="100">
          <template #default="{ row }">
            <el-tag type="warning">{{ row.points }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active === 1 ? 'success' : 'danger'">
              {{ row.is_active === 1 ? '正常' : '封禁' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleRecharge(row)">
              <el-icon><Wallet /></el-icon>
              充值
            </el-button>
            <el-button
              :type="row.is_active === 1 ? 'danger' : 'success'"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.is_active === 1 ? '封禁' : '解封' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        :page-size="20"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: flex-end;"
        @current-change="loadUsers"
      />
    </el-card>

    <!-- 充值弹窗 -->
    <el-dialog v-model="rechargeDialogVisible" title="积分充值" width="400px">
      <el-form :model="rechargeForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input :value="rechargeForm.username" disabled />
        </el-form-item>
        <el-form-item label="当前积分">
          <el-input :value="rechargeForm.currentPoints" disabled />
        </el-form-item>
        <el-form-item label="充值数量">
          <el-input-number v-model="rechargeForm.amount" :min="1" :max="10000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rechargeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRecharge" :loading="recharging">
          确认充值
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const loading = ref(false)
const users = ref([])
const searchKeyword = ref('')
const page = ref(1)
const total = ref(0)

const rechargeDialogVisible = ref(false)
const recharging = ref(false)
const rechargeForm = reactive({
  username: '',
  currentPoints: 0,
  amount: 100
})

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/users', {
      params: {
        keyword: searchKeyword.value,
        page: page.value
      }
    })
    users.value = res.items || res
    total.value = res.total || users.value.length
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 打开充值弹窗
const handleRecharge = (row) => {
  rechargeForm.username = row.username
  rechargeForm.currentPoints = row.points
  rechargeForm.amount = 100
  rechargeDialogVisible.value = true
}

// 确认充值
const confirmRecharge = async () => {
  recharging.value = true
  try {
    await request.post('/admin/recharge', null, {
      params: {
        username: rechargeForm.username,
        amount: rechargeForm.amount
      }
    })
    ElMessage.success(`成功充值 ${rechargeForm.amount} 积分`)
    rechargeDialogVisible.value = false
    loadUsers()
  } catch (error) {
    console.error(error)
  } finally {
    recharging.value = false
  }
}

// 封禁/解封
const handleToggleStatus = async (row) => {
  const action = row.is_active === 1 ? '封禁' : '解封'

  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${row.username}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await request.post(`/admin/users/${row.id}/toggle-status`)
    ElMessage.success(`${action}成功`)
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>