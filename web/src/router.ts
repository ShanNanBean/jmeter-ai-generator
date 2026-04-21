import { createWebHashHistory, createRouter } from 'vue-router';
import InputView from './views/InputView.vue';
import PreviewView from './views/PreviewView.vue';
import EditView from './views/EditView.vue';
import ResultView from './views/ResultView.vue';

const router = createRouter({
  history: createWebHashHistory(),  // Hash mode — required for iframe
  routes: [
    { path: '/', name: 'input', component: InputView },
    { path: '/preview', name: 'preview', component: PreviewView },
    { path: '/edit', name: 'edit', component: EditView },
    { path: '/result', name: 'result', component: ResultView },
  ],
});

export default router;