<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import mermaid from 'mermaid';

const props = defineProps<{
  activeNode: string | null;
}>();

const container = ref<HTMLElement | null>(null);

// Static definition of our specific graph
const baseGraph = `
graph TD
  START((Start)) --> Supervisor
  Supervisor{Supervisor}
  
  Supervisor -->|next=Researcher| Researcher[Researcher]
  Supervisor -->|next=Writer| Writer[Writer]
  
  Researcher --> Supervisor
  Writer --> Supervisor
  
  Supervisor -->|next=FINISH| END((End))
  
  classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
  classDef active fill:#ffeb3b,stroke:#fbc02d,stroke-width:3px,color:#000;
`;

const renderGraph = async () => {
    if (!container.value) return;
    
    // Inject class for active node
    let graphDef = baseGraph;
    if (props.activeNode) {
        graphDef += `\n class ${props.activeNode} active;`;
    }
    
    try {
        const { svg } = await mermaid.render('mermaid-graph', graphDef);
        container.value.innerHTML = svg;
    } catch (e) {
        console.error("Mermaid error", e);
    }
};

onMounted(() => {
    mermaid.initialize({ startOnLoad: false, theme: 'dark' });
    renderGraph();
});

watch(() => props.activeNode, () => {
    renderGraph();
});

</script>

<template>
  <div class="w-full h-full flex items-center justify-center bg-card rounded-lg border shadow-sm p-4 overflow-hidden">
    <div ref="container" class="w-full h-full flex items-center justify-center"></div>
  </div>
</template>
