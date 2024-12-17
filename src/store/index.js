import { createStore } from 'vuex';
import { toRaw } from 'vue';

export default createStore({
    state() {
        return {
            receivedMeshData: null,
            parameters: {
                inputs: [],
                formatted: [],
            },
            sidebarOpen: true,
            allMessages: [],
            chatMessages: [],
            responseMessages: [],
            responseObjects: [],
            prompt: "",
            isThinking: false,
            currentTab: "Parameters",
            theme: 'dark', // Default theme
            geometryLoading: false,
            username: localStorage.getItem('chat_username') || '',
            websocketUrl: localStorage.getItem('websocket_url') || 'http://localhost:5001',
        };
    },
    mutations: {
        setTheme(state, theme) {
            state.theme = theme;
        },
        setUsername(state, username) {
            state.username = username;
            localStorage.setItem('chat_username', username);
        },
        setWebsocketUrl(state, url) {
            state.websocketUrl = url;
            localStorage.setItem('websocket_url', url);
        },
        setGeometryLoading(state, value) {
            state.geometryLoading = value;
        },
        setCurrentTab(state, tab) {
            state.currentTab = tab;
        },
        setPrompt(state, prompt) {
            state.prompt = prompt;
        },
        addMessage(state, { text, username }) {
            const msg = { text, type: "user", sender: username || 'User' };
            state.chatMessages.push(msg);
            state.allMessages.push(msg);
        },
        addUserMessage(state, { text, username }) {
            // Used for messages broadcast from server (handles multi-client sync)
            const msg = { text, type: "user", sender: username || 'User' };
            state.chatMessages.push(msg);
            state.allMessages.push(msg);
        },
        addResponseMessage(state, message) {
            const msg = { text: message, type: "response", sender: "Assistant" };
            state.responseMessages.push(msg);
            state.allMessages.push(msg);
        },
        addAllMessages(state, message) {
            state.allMessages.push(message);
        },
        addResponseObject(state, responseObject) {
            const text = `Changed ${responseObject.name} to ${responseObject.value} ✅`;
            const msg = { text, type: "response", sender: "Assistant" };
            state.responseMessages.push(msg);
            state.allMessages.push(msg);
        },
        setReceivedMeshData(state, data) {
            state.receivedMeshData = data;
            console.log("Received mesh data: ", state.receivedMeshData);
        },
        setParameters(state, inputs) {
            // Ensure we have both name and label properties for compatibility
            state.parameters.inputs = inputs.map((input, index) => ({
                ...input,
                id: index,
                name: input.name || input.label, // Use name if available, fallback to label
                label: input.label || input.name // Use label if available, fallback to name
            }));
            this.commit('formatApiParameters');
        },
        formatApiParameters(state) {
            state.parameters.formatted = state.parameters.inputs.map(input => ({
                ParamName: "RH_IN:" + input.name,
                InnerTree: {
                    "{0; }": [{
                        type: "System.Double",
                        data: (input.value ?? 0).toString(),
                    }]
                }
            }));
        },
        updateParameterValue(state, { id, value }) {
            console.log(`[store] updateParameterValue called with id: ${id}, value: ${value}`);
            const index = state.parameters.inputs.findIndex(input => input.id === id);
            if (index !== -1) {
                console.log(`[store] Found parameter at index ${index}:`, state.parameters.inputs[index]);
                state.parameters.inputs.splice(index, 1, { ...state.parameters.inputs[index], value: value });
                console.log(`[store] Updated parameter at index ${index}:`, state.parameters.inputs[index]);
                state.parameters.formatted = state.parameters.inputs.map(input => ({
                    ParamName: "RH_IN:" + input.name,
                    InnerTree: {
                        "{0; }": [{
                            type: "System.Double",
                            data: (input.value ?? 0).toString(),
                        }]
                    }
                }));
                console.log(`[store] New formatted parameters:`, state.parameters.formatted);
            } else {
                console.log(`[store] updateParameterValue: Parameter with id ${id} not found`);
            }
        },
        updateParameterByName(state, { name, value }) {
            console.log(`[store] updateParameterByName called with name: ${name}, value: ${value}`);
            const index = state.parameters.inputs.findIndex(input => 
                input.name === name || input.label === name
            );
            if (index !== -1) {
                console.log(`[store] Found parameter at index ${index}:`, state.parameters.inputs[index]);
                state.parameters.inputs.splice(index, 1, { ...state.parameters.inputs[index], value: value });
                console.log(`[store] Updated parameter at index ${index}:`, state.parameters.inputs[index]);
                state.parameters.formatted = state.parameters.inputs.map(input => ({
                    ParamName: "RH_IN:" + input.name,
                    InnerTree: {
                        "{0; }": [{
                            type: "System.Double",
                            data: (input.value ?? 0).toString(),
                        }]
                    }
                }));
                console.log(`[store] New formatted parameters:`, state.parameters.formatted);
            } else {
                console.log(`[store] updateParameterByName: Parameter not found for name: ${name}`);
            }
        },
        toggleSidebar(state) {
            state.sidebarOpen = !state.sidebarOpen;
        },
        setSidebarOpen(state, value) {
            state.sidebarOpen = value;
        },
        setThinking(state, value) {
            state.isThinking = value;
        },
    },
    actions: {
        handleParameterUpdate({ commit }, { id, value }) {
            commit('updateParameterValue', { id, value });
        },
        updateParameterByName({ commit }, { name, value }) {
            commit('updateParameterByName', { name, value });
        },
    },
    getters: {
        theme(state) { // Add this getter
            return state.theme;
        },
    }
});
