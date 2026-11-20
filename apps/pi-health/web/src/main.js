import "@fontsource-variable/archivo/wdth.css";
import "uplot/dist/uPlot.min.css";
import "./app.css";
import "./anime.css";
import { mount } from "svelte";
import App from "./App.svelte";

mount(App, { target: document.getElementById("app") });
