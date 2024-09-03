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
            state.parameters.inputs = inputs;
        },
        addMessage(state, message) {
            state.chatMessages.push(message);
        },
        setPrompt(state, prompt) {
            state.prompt = prompt;
        },
    },
});
