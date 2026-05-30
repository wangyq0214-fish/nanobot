<template>
  <div class="section-basic-info">
    <h2 v-if="section.title">{{ section.title }}</h2>
    <table v-if="section.data">
      <thead>
        <tr><th>项目</th><th>内容</th></tr>
      </thead>
      <tbody>
        <tr v-for="(val, key) in section.data" :key="key">
          <td>{{ key }}</td>
          <td>{{ val }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({ section: { type: Object, required: true } })
</script>
