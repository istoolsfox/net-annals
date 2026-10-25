// 纹理与音频走 webpack 资源管线（import），绕过静态文件服务
import cardOpen from '../public/textures/card-open.png';
import entitiesTencent from '../public/textures/entities-tencent.png';
import entitiesTop from '../public/textures/entities-top.png';
import github from '../public/textures/github.png';
import hero from '../public/textures/hero.png';
import personsTop from '../public/textures/persons-top.png';
import tl1972 from '../public/textures/tl-1972.png';
import tl1994 from '../public/textures/tl-1994.png';
import tl2003 from '../public/textures/tl-2003.png';
import tl2010 from '../public/textures/tl-2010.png';
import tl2020 from '../public/textures/tl-2020.png';
import todayDrawer from '../public/textures/today-drawer.png';
import todayList from '../public/textures/today-list.png';
import worksTop from '../public/textures/works-top.png';
import appleIcon from '../public/assets/apple-touch-icon.png';
import bgm from '../public/audio/bgm-tech-house.mp3';

export const TEX = {
  'card-open': cardOpen, 'entities-tencent': entitiesTencent, 'entities-top': entitiesTop,
  github, hero, 'persons-top': personsTop,
  'tl-1972': tl1972, 'tl-1994': tl1994, 'tl-2003': tl2003, 'tl-2010': tl2010, 'tl-2020': tl2020,
  'today-drawer': todayDrawer, 'today-list': todayList, 'works-top': worksTop,
};
export { appleIcon, bgm };
