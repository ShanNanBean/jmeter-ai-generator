import { createWebHashHistory, createRouter } from 'vue-router';
import InputView from './views/InputView.vue';
import PreviewView from './views/PreviewView.vue';
import EditView from './views/EditView.vue';
import ResultView from './views/ResultView.vue';
import { useGenerationStore } from './stores/generation';

const router = createRouter({
  history: createWebHashHistory(),  // Hash mode — required for iframe
  routes: [
    { path: '/', name: 'input', component: InputView },
    { path: '/preview', name: 'preview', component: PreviewView },
    { path: '/edit', name: 'edit', component: EditView },
    { path: '/result', name: 'result', component: ResultView },
  ],
});

router.beforeEach((to) => {
  const store = useGenerationStore();
  if ((to.name === 'preview' || to.name === 'edit') && !store.ir) {
    return { name: 'input' };
  }
  if (to.name === 'result' && !store.jmx) {
    return store.ir ? { name: 'edit' } : { name: 'input' };
  }
});

export default router;
