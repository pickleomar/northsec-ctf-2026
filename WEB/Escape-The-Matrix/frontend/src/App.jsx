import React, { useRef, useEffect } from "react";
import "./App.css";
import MatrixCard from "./components/MatrixCard";

const CHAR_POOL =
  "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZあアカサタナハマヤラワ!@#$%&*+-=<>?";

export default function App() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl =
      canvas.getContext("webgl", { antialias: false, alpha: false }) ||
      canvas.getContext("experimental-webgl");
    if (!gl) return;

    function resize() {
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      const w = window.innerWidth;
      const h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      gl.viewport(0, 0, canvas.width, canvas.height);
    }
    resize();
    window.addEventListener("resize", resize);

    const vs = `
      attribute vec2 a_pos;
      varying vec2 v_uv;
      void main(){
        v_uv = a_pos * 0.5 + 0.5;
        gl_Position = vec4(a_pos,0.0,1.0);
      }
    `;

    const fs = `
      precision mediump float;
      varying vec2 v_uv;
      uniform float u_time;
      uniform vec2 u_resolution;
      uniform sampler2D u_texture;
      uniform float u_cols;
      uniform float u_rows;

      float hash(vec2 p){
        p = fract(p*vec2(127.1,311.7));
        p += dot(p,p+34.5);
        return fract(p.x*p.y);
      }

      vec3 rayDir(vec2 p){
        return normalize(vec3(p.x, p.y-0.05, 1.3));
      }

      float intersectPlane(vec3 ro, vec3 rd, vec3 n, float d){
        float denom = dot(rd,n);
        if(abs(denom)<1e-5) return -1.0;
        return -(dot(ro,n)+d)/denom;
      }

      vec4 sampleAtlas(int idx, vec2 uv){
        float fi = float(idx);
        float cx = mod(fi,u_cols);
        float cy = floor(fi/u_cols);
        vec2 atlasUV = (vec2(cx,cy)+uv)/vec2(u_cols,u_rows);
        return texture2D(u_texture,atlasUV);
      }

      int pickChar(vec2 id){
        float h = hash(id);
        return int(floor(h*(u_cols*u_rows-1.0)));
      }

      void main(){
        vec2 p = (v_uv*2.0-1.0)*vec2(u_resolution.x/u_resolution.y,1.0);
        vec3 ro = vec3(0.0,0.0,-0.6);
        vec3 rd = rayDir(p);

        vec3 col = vec3(0.0,0.02,0.0);

        float tMin = 1e9;
        vec3 hit;
        int plane = 0;

        float t;

        t = intersectPlane(ro,rd,vec3(0,0,1),-2.2);
        if(t>0.0 && t<tMin){
          vec3 p3 = ro+rd*t;
          if(abs(p3.x)<=1.4 && abs(p3.y)<=0.9){
            tMin=t; hit=p3; plane=1;
          }
        }

        t = intersectPlane(ro,rd,vec3(1,0,0),1.4);
        if(t>0.0 && t<tMin){
          vec3 p3 = ro+rd*t;
          if(p3.z>=0.15 && p3.z<=2.2 && abs(p3.y)<=0.9){
            tMin=t; hit=p3; plane=2;
          }
        }

        t = intersectPlane(ro,rd,vec3(-1,0,0),1.4);
        if(t>0.0 && t<tMin){
          vec3 p3 = ro+rd*t;
          if(p3.z>=0.15 && p3.z<=2.2 && abs(p3.y)<=0.9){
            tMin=t; hit=p3; plane=3;
          }
        }

        t = intersectPlane(ro,rd,vec3(0,1,0),0.9);
        if(t>0.0 && t<tMin){
          vec3 p3 = ro+rd*t;
          if(abs(p3.x)<=1.4 && p3.z>=0.15 && p3.z<=2.2){
            tMin=t; hit=p3; plane=4;
          }
        }

        t = intersectPlane(ro,rd,vec3(0,-1,0),0.9);
        if(t>0.0 && t<tMin){
          vec3 p3 = ro+rd*t;
          if(abs(p3.x)<=1.4 && p3.z>=0.15 && p3.z<=2.2){
            tMin=t; hit=p3; plane=5;
          }
        }

        if(plane>0){
          vec2 uv;
          if(plane==1) uv = vec2((hit.x+1.4)/2.8,(hit.y+0.9)/1.8);
          else if(plane==2) uv = vec2((hit.z-0.15)/2.05,(hit.y+0.9)/1.8);
          else if(plane==3) uv = vec2((2.2-hit.z)/2.05,(hit.y+0.9)/1.8);
          else if(plane==4) uv = vec2((hit.x+1.4)/2.8,(hit.z-0.15)/2.05);
          else uv = vec2((hit.x+1.4)/2.8,(2.2-hit.z)/2.05);

          float tilesX = 36.0;
          float tilesY = plane>=4 ? 22.0 : 60.0;

          vec2 tile = uv*vec2(tilesX,tilesY);
          vec2 id = floor(tile);
          vec2 f = fract(tile);

          float scroll = u_time*0.25;
          f.y = fract(f.y + scroll);

          int idx = pickChar(id);
          vec4 g = sampleAtlas(idx,f);

          float depth = clamp(1.0-tMin/3.0,0.0,1.0);
          float a = g.a*(0.4+depth);

          col = mix(col, vec3(0.0,1.0,0.3)*a, a);
        }

        float vign = smoothstep(1.1,0.3,length(v_uv-0.5));
        col *= vign;

        gl_FragColor = vec4(col,1.0);
      }
    `;

    function compile(src,type){
      const s = gl.createShader(type);
      gl.shaderSource(s,src);
      gl.compileShader(s);
      return s;
    }

    const prog = gl.createProgram();
    gl.attachShader(prog,compile(vs,gl.VERTEX_SHADER));
    gl.attachShader(prog,compile(fs,gl.FRAGMENT_SHADER));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER,quad);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([
      -1,-1,1,-1,-1,1,
      -1,1,1,-1,1,1
    ]),gl.STATIC_DRAW);

    const loc = gl.getAttribLocation(prog,"a_pos");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);

    function buildAtlas(){
      const chars = CHAR_POOL.split("");
      const cols = 16;
      const rows = Math.ceil(chars.length/cols);
      const size = 64;
      const c = document.createElement("canvas");
      c.width = cols*size;
      c.height = rows*size;
      const x = c.getContext("2d");
      x.font = "48px monospace";
      x.textAlign="center";
      x.textBaseline="middle";
      for(let i=0;i<chars.length;i++){
        const cx=i%cols;
        const cy=(i/cols)|0;
        x.fillStyle="#bfffd0";
        x.fillText(chars[i],cx*size+size/2,cy*size+size/2);
      }
      const t = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D,t);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
      gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,c);
      return {t,cols,rows};
    }

    const atlas = buildAtlas();

    gl.uniform1i(gl.getUniformLocation(prog,"u_texture"),0);
    gl.uniform1f(gl.getUniformLocation(prog,"u_cols"),atlas.cols);
    gl.uniform1f(gl.getUniformLocation(prog,"u_rows"),atlas.rows);

    let simTime = 0;
    let last = performance.now();
    const SPEED = 2.9;

    function render(){
      const now = performance.now();
      const dt = (now-last)*0.001;
      last = now;
      simTime += dt*SPEED;

      gl.uniform1f(gl.getUniformLocation(prog,"u_time"),simTime);
      gl.uniform2f(
        gl.getUniformLocation(prog,"u_resolution"),
        canvas.width,
        canvas.height
      );
      gl.drawArrays(gl.TRIANGLES,0,6);
      requestAnimationFrame(render);
    }

    render();

    return ()=>window.removeEventListener("resize",resize);
  }, []);

  return (
    <div className="App">
      <canvas ref={canvasRef} className="matrix-canvas"/>
      <MatrixCard />
    </div>
  );
}
