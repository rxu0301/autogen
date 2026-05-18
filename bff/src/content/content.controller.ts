import { Controller, Post, Get, Body, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiQuery } from '@nestjs/swagger';
import { ContentService } from './content.service';
import {
  NewsSearchDto,
  SummaryGenerateDto,
  ScriptGenerateDto,
  ThumbnailPromptDto,
  SaveResultDto,
  LibraryQueryDto,
} from './content.dto';

@ApiTags('news')
@Controller('news')
export class ContentController {
  constructor(private readonly contentService: ContentService) {}

  /** Step 1: 뉴스 검색 */
  @Post('search')
  @ApiOperation({ summary: '주제 기반 최신 뉴스 검색 (RAG)' })
  @ApiResponse({ status: 200, description: '뉴스 3개 반환' })
  searchNews(@Body() dto: NewsSearchDto) {
    return this.contentService.searchNews(dto);
  }

  /** Step 2-A: 요약본 생성 */
  @Post('summary')
  @ApiOperation({ summary: '뉴스 요약본 생성 (500~900자, 3가지 버전)' })
  @ApiResponse({ status: 200, description: '요약본 3가지 버전 반환' })
  generateSummary(@Body() dto: SummaryGenerateDto) {
    return this.contentService.generateSummary(dto);
  }

  /** Step 2-B: 스크립트 생성 */
  @Post('script')
  @ApiOperation({ summary: '뉴스 요약 스크립트 생성 (3가지 버전)' })
  @ApiResponse({ status: 200, description: '스크립트 3가지 버전 반환' })
  generateScript(@Body() dto: ScriptGenerateDto) {
    return this.contentService.generateScript(dto);
  }

  /** Step 3: 썸네일 프롬프트 생성 */
  @Post('thumbnail')
  @ApiOperation({ summary: '뉴스 썸네일 이미지 생성 프롬프트 (3가지 버전)' })
  @ApiResponse({ status: 200, description: '썸네일 프롬프트 3가지 반환' })
  generateThumbnail(@Body() dto: ThumbnailPromptDto) {
    return this.contentService.generateThumbnail(dto);
  }

  /** Step 4: 결과 저장 */
  @Post('save')
  @ApiOperation({ summary: '생성 결과를 라이브러리에 저장' })
  @ApiResponse({ status: 201, description: '저장 성공' })
  saveResult(@Body() dto: SaveResultDto) {
    return this.contentService.saveResult(dto);
  }

  /** Step 5: 라이브러리 조회 */
  @Get('library')
  @ApiOperation({ summary: '라이브러리 조회 (해시태그 필터 가능)' })
  @ApiQuery({ name: 'hashtag', required: false })
  @ApiQuery({ name: 'limit', required: false })
  @ApiResponse({ status: 200, description: '저장된 결과 목록 반환' })
  getLibrary(@Query() query: LibraryQueryDto) {
    return this.contentService.getLibrary(query);
  }

  /** 헬스 체크 */
  @Get('health')
  @ApiOperation({ summary: '백엔드 헬스 체크' })
  health() {
    return this.contentService.health();
  }
}
