import { createStore } from 'vuex';

export default createStore({
    state() {
        return {
            parameters: {
                inputs: [],
            },
            chatMessages: [],
            prompt: "",
        };
    },
    mutations: {
        setParameters(state, inputs) {
            state.parameters.inputs = inputs.map((input, index) => ({
                ...input,
                id: index,
                name: input.name || input.label,
                label: input.label || input.name,
            }));
        },
        updateParameterValue(state, { id, value }) {
            const index = state.parameters.inputs.findIndex(i => i.id === id);
            if (index !== -1) {
                state.parameters.inputs[index].value = value;
            }
        },
        addMessage(state, message) {
            state.chatMessages.push(message);
        },
        setPrompt(state, prompt) {
            state.prompt = prompt;
        },
    },
});
