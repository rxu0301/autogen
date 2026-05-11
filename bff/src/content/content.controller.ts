import { Controller, Post, Get, Body } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { ContentService } from './content.service';
import { GenerateContentDto, SimilarContentDto } from './content.dto';

@ApiTags('content')
@Controller('content')
export class ContentController {
  constructor(private readonly contentService: ContentService) {}

  @Post('generate')
  @ApiOperation({ summary: '숏폼 콘텐츠 생성' })
  @ApiResponse({ status: 200, description: '콘텐츠 생성 성공' })
  @ApiResponse({ status: 400, description: '잘못된 요청' })
  @ApiResponse({ status: 502, description: '백엔드 오류' })
  @ApiResponse({ status: 503, description: '백엔드 서비스 불가' })
  generate(@Body() dto: GenerateContentDto) {
    return this.contentService.generate(dto);
  }

  @Post('similar')
  @ApiOperation({ summary: '유사 콘텐츠 검색' })
  @ApiResponse({ status: 200, description: '검색 성공' })
  @ApiResponse({ status: 400, description: '잘못된 요청' })
  @ApiResponse({ status: 503, description: '백엔드 서비스 불가' })
  findSimilar(@Body() dto: SimilarContentDto) {
    return this.contentService.findSimilar(dto);
  }

  @Get('health')
  @ApiOperation({ summary: '백엔드 헬스 체크' })
  @ApiResponse({ status: 200, description: '정상' })
  @ApiResponse({ status: 503, description: '백엔드 서비스 불가' })
  health() {
    return this.contentService.health();
  }
}
