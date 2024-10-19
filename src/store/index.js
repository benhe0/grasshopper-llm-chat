import { createStore } from 'vuex';

export default createStore({
    state() {
        return {
            parameters: {
                inputs: [],
            },
            chatMessages: [],
            prompt: "",
            isThinking: false,
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
        addMessage(state, { text, type }) {
            state.chatMessages.push({ text, type: type || "user" });
        },
        addResponse(state, text) {
            state.chatMessages.push({ text, type: "response" });
        },
        setPrompt(state, prompt) {
            state.prompt = prompt;
        },
        setThinking(state, value) {
            state.isThinking = value;
        },
    },
});
